"""
UnifiedActivatedSludgeProcess - Procédé unifié supportant ASM et ML
"""
import numpy as np
import logging

from typing import Dict, Any, List, Optional

from core.process.process_node import ProcessNode
from processes.sludge_process.sludge_metrics import SludgeMetrics
from processes.sludge_process.sludge_model_adapter import SludgeModelAdapter
from core.model.model_registry import ModelRegistry
from core.solver.cstr_solver import CSTRSolver

logger = logging.getLogger(__name__)

class UnifiedActivatedSludgeProcess(ProcessNode):
    """
    Procédé unifié de boues activées supportant :
    - Modèle mécanistes (ASM1, ASM2d, ASM3)
    - Modèle ML (Linear, RandomForest, RNN)
    """

    def __init__(self, node_id: str, name: str, config: Dict[str, Any]) -> None:
        """
        Initialise le processus

        Args:
            node_id (str): Identifiant unique
            name (str): Nom du procédé
            config (Dict[str, Any]): Configuration contenant :
                - volume : Volume du bassin
                - dissolved_oxygen_setpoint : Consigne DO
                - model : Modèle à utiliser (ASM1Model, LinearModel, etc)
                - model_parameters : Paramètres du modèles
                - depth : Profondeur
                - recycle_ratio : Ratio de recyclage
                - waste_ratio : Ratio de purge
                - model_path : Chemin vers modèle pré-entraîné (ML uniquement)
        """
        super().__init__(node_id, name, config)

        self.volume = config.get('volume', 5000.0)
        self.depth = config.get('depth', 4.0)
        self.do_setpoint = config.get('dissolved_oxygen_setpoint', 2.0)
        self.recycle_ratio = config.get('recycle_ratio', 1.0)
        self.waste_ratio = config.get('waste_ratio', 0.01)
        self.use_calibration = config.get('use_calibration', True)

        model_type = config.get('model', 'ASM1Model')
        model_params = config.get('model_parameters', {})
        model_path = config.get('model_path', None)

        registry = ModelRegistry.get_instance()

        try:
            self.model_instance = registry.create_model(
                model_type=model_type,
                params=model_params,
                model_path=model_path
            )
            self.model_type = model_type
            self.logger.info(f"Modèle chargé : {model_type}")
        except ValueError as e:
            self.logger.error(f"Erreur de chargement du modèle : {e}")
            raise

        self.is_empyrical = model_type.endswith('Model') and 'ASM' in model_type.upper()
        self.is_ml = not self.is_empyrical

        if self.is_empyrical:
            self._init_mechanistric()
        else:
            self._init_ml()

        self.logger.info(
            f"{self} initilisé - Type : {'Mécaniste' if self.is_empyrical else 'ML'}"
        )

    def _init_mechanistric(self) -> None:
        """Initialisation spécifique pour modèles mécanistes (ASM)"""
        model_name = self.model_type.replace('Model', '').upper()
        self.model_adapter = SludgeModelAdapter(self.model_instance, model_name)

        self.concentrations = np.zeros(self.model_adapter.size)

        registry = ModelRegistry.get_instance()
        self.sludge_metrics = SludgeMetrics(self.model_type, registry)

        self.logger.debug("Initialisation mécaniste terminée")

    def _init_ml(self) -> None:
        """Initialisation spécifique pour modèles ML"""
        self.state_buffer = []
        self.feature_names = self.model_instance.feature_names
        self.target_names = self.model_instance.target_names

        self.sludge_metrics = None

        self.logger.debug("Initialisation ML terminée")

    def initialize(self) -> None:
        """Initialise l'état du bassin selon le type de modèle"""
        if self.is_empyrical:
            self._initialize_empyrical()
        else:
            self._initialize_ml()

    def _initialize_empyrical(self) -> None:
        """Initialisation pour modèles ASM"""
        init_state = self.model_adapter.initial_state(
            do_setpoint=self.do_setpoint,
            process_id=self.node_id,
            use_calibration=self.use_calibration,
            process_config=self.config
        )
        self.concentrations = self.model_adapter.dict_to_vector(init_state)
        self.state = init_state
        self.logger.info("Etat initial ASM configuré")

    def _initialize_ml(self) -> None:
        """Initialisation pour modèles ML"""
        #FIXME attention à ces valeurs
        self.state = self.model_instance.initialize_state({
            'cod': 100.0,
            'ss': 2000.0,
            'nh4': 2.0,
            'no3': 5.0,
            'po4': 1.0,
            'biomass': 2000.0
        })
        self.state_buffer = []
        self.logger.info("Etat initial ML configuré")

    def get_required_inputs(self) -> List[str]:
        """Inputs requis"""
        return ['flow', 'flowrate', 'temperature']
    
    def process(self, inputs: Dict[str, Any], dt: float) -> Dict[str, Any]:
        """
        Traite un pas de temps

        Args:
            inputs (Dict[str, Any]): Données d'entrée
            dt (float): Pas de temps

        Returns:
            Dict[str, Any]: Sorties du procédé
        """
        if self.is_empyrical:
            return self._process_empyrical(inputs, dt)
        else:
            return self._process_ml(inputs, dt)
        
    def _process_empyrical(self, inputs: Dict[str, Any], dt: float) -> Dict[str, Any]:
        """Traitement avec modèle ASM"""
        inputs = self.fractionate_input(inputs, target_model=self.model_adapter.name)

        q_in = inputs['flowrate']
        temperature = inputs['temperature']
        inflow_components = self.model_adapter.dict_to_vector(inputs['components'])

        c_out = self._simulate_reactor(inflow_components, q_in, dt)

        comp_out = self.model_adapter.vector_to_dict(c_out)
        
        assert self.sludge_metrics is not None
        results = self.sludge_metrics.compute(
            comp_out, inflow_components, q_in, dt, self.volume, temperature
        )

        self.concentrations = c_out
        self.state = comp_out
        self.outputs = results

        self.metrics = {
            'cod_removal': results['cod_removal_rate'],
            'hr': results['hrt_hours'],
            'mlss': results['ss'],
            'energy_kwh': results['aeration_energy_kwh']
        }

        return results
    
    def _simulate_reactor(self, c_in: np.ndarray, q_in: float, dt: float) -> np.ndarray:
        """Simulation CSTR pour modèles mécanistes"""
        c = self.concentrations.copy()
        hrt_h = self.volume / q_in
        dilution = 1.0 / (hrt_h / 24.0) if hrt_h > 0 else 0
        dt_day = dt / 24.0

        oxygen_idx = None
        if self.model_adapter.name == 'ASM1':
            oxygen_idx = self.model_adapter.model.COMPONENT_INDICES.get('so')
        else:
            oxygen_idx = self.model_adapter.model.COMPONENT_INDICES.get('so2')

        c_next = CSTRSolver.solve_step(
            c=c,
            c_in=c_in,
            reaction_func=self.model_adapter.reactions,
            dt=dt_day,
            dilution_rate=dilution,
            method='rk4',
            oxygen_idx=oxygen_idx,
            do_setpoint=self.do_setpoint
        )

        return c_next
    
    def _process_ml(self, inputs: Dict[str, Any], dt: float) -> Dict[str, Any]:
        """Traitement avec modèle ML"""
        features = self._extract_ml_features(inputs)

        predictions = self.model_instance.predict_step(
            current_state=self.state,
            inputs=features,
            dt=dt
        )

        results = self._compute_ml_metrics(predictions, features, dt)

        self.state.update(predictions)
        self.outputs = results

        self.metrics = {
            'cod_removal': results.get('cod_removal', 0),
            'hrt': results.get('hrt_hours', 0),
            'mlss': results.get('ss', 0),
            'energy_kwh': results.get('aeration_energy_kwh', 0)
        }

        return results
    
    def _extract_ml_features(self, inputs: Dict[str, Any]) -> Dict[str, float]:
        """Extrait les features pour les modèles ML"""
        flow = inputs.get('flow')
        features = {
            'flowrate': inputs.get('flowrate', 0),
            'temperature': inputs.get('temperature', 20),
            'volume': self.volume,
            'hrt_hours': self.volume / inputs.get('flowrate', 1) if inputs.get('flowrate', 0) > 0 else 0,
            'srt_days': self.state.get('srt_days', 10)
        }

        if flow:
            features.update({
                'cod_in': flow.cod,
                'ss_in': flow.ss,
                'nh4_in': flow.nh4,
                'no3_in': flow.no3,
                'po4_in': flow.po4
            })

        for name in self.target_names:
            if name in self.state:
                features[name] = self.state[name]

        return features
    
    def _compute_ml_metrics(
            self,
            predictions: Dict[str, float],
            features: Dict[str, float],
            dt: float
    ) -> Dict[str, Any]:
        """Calcule les métriques pour les modèles ML"""
        cod_out = predictions.get('cod', 0)
        cod_in = features.get('cod_in', 0)
        q_in = features.get('flowrate', 0)

        cod_removal = 0
        if cod_in > 0:
            cod_removal = ((cod_in - cod_out) / cod_in) * 100

        oxygen_consumed = (cod_in - cod_out) * q_in *dt / 1000.0
        energy = oxygen_consumed * 2.0

        results = {
            'flowrate': q_in,
            'temperature': features.get('temperature', 20),
            'model_type': self.model_type,
            'components': predictions,

            'cod': cod_out,
            'ss': predictions.get('ss', 0),
            'nh4': predictions.get('nh4', 0),
            'no3': predictions.get('no3', 0),
            'po4': predictions.get('po4', 0),
            'biomass_concentration': predictions.get('biomass', 0),

            'cod_removal_rate': cod_removal,
            'cod_removal': predictions.get('cod_removal', cod_removal),
            'hrt_hours': features.get('hrt_hours', 0),
            'srt_days': features.get('srt_days', 10),

            'oxygen_consumed_kg': oxygen_consumed,
            'aeration_energy_kwh': energy,
            'energy_per_m3': energy / (q_in * dt) if q_in > 0 else 0
        }

        return results
    
    def update_state(self, outputs: Dict[str, Any]) -> None:
        """Met à jour l'état interne"""
        if self.is_empyrical:
            self.state = outputs.get('components', {}).copy()
        else:
            self.state.update(outputs.get('components', {}))

        self.outputs = outputs

    def __repr__(self) -> str:
        model_info = f"ASM={self.model_adapter.name}" if self.is_empyrical else f"ML={self.model_type}"
        return f"<UnifiedActivatedSludgeProcess {self.name} [{model_info}] V={self.volume}m^3>"