"""
ActivatedSludgeProcess - Procédé générique de boues activées
"""
import numpy as np
import logging

from typing import Dict, Any, List

from core.process.process_node import ProcessNode
from processes.sludge_process.sludge_metrics import SludgeMetrics
from processes.sludge_process.sludge_model_adapter import SludgeModelAdapter
from core.model.model_registry import ModelRegistry

from core.solver.cstr_solver import CSTRSolver

logger = logging.getLogger(__name__)

class ActivatedSludgeProcess(ProcessNode):
    """
    Procédé générique de traitement par boues activées
    """

    def __init__(self, node_id: str, name: str, config: Dict[str, Any]) -> None:
        """
        Initialise le processus de boues activées

        Args:
            node_id (str): Identifiant unique
            name (str): Nom du procédé
            config (Dict[str, Any]): Configuration contenant :
                - volume : Volume du bassin (m^3)
                - dissolved_oxygen_setpoint : Consigne DO (mg/L)
                - model : Modèle à utiliser
                - model_parameters : Paramètres spécifiques au modèle
                - depth : Profondeur (m)
                - recycle_ratio : Ratio de recyclage Qr/Qin
                - waste_ratio : Ratio de purge Qw/Qin
        """
                
        super().__init__(node_id, name, config)

        self.volume = config.get('volume', 5000.0)
        self.depth = config.get('depth', 4.0)
        self.do_setpoint = config.get('dissolved_oxygen_setpoint', 2.0)
        self.recycle_ratio = config.get('recycle_ratio', 1.0)
        self.waste_ratio = config.get('waste_ratio', 0.01)

        self.use_calibration = config.get('use_calibration', True)

        model_type = config.get('model', 'ASM1')
        model_param = config.get('model_parameters', {})

        registry = ModelRegistry.get_instance()

        try:
            self.model_instance = registry.create_model(
                model_type=model_type,
                params=model_param
            )
            self.model_type = model_type
            self.logger.info(f"Modèle chargé : {model_type}")
        except ValueError as e:
            self.logger.error(f"Erreur de chargement du modèle : {e}")
            raise

        model_name = model_type.replace('Model', '').upper()
        self.model_adapter = SludgeModelAdapter(self.model_instance, model_name)
        
        self.concentrations = np.zeros(self.model_adapter.size)
        self.sludge_metrics = SludgeMetrics(self.model_type, registry)
        self.logger.info(f"{self} initialisé avec modèle {model_type}")
    
    def initialize(self) -> None:
        """Initialise l'état du bassin"""
        init_state = self.model_adapter.initial_state(
            do_setpoint=self.do_setpoint,
            process_id=self.node_id,
            use_calibration=self.use_calibration,
            process_config=self.config
        )
        self.concentrations = self.model_adapter.dict_to_vector(init_state)
        self.state = init_state

    def get_required_inputs(self) -> List[str]:
        return ['flow', 'flowrate', 'temperature']
    
    def process(self, inputs: Dict[str, Any], dt: float) -> Dict[str, Any]:
        """Exécute un pas de simulation pour le procédé"""
        inputs = self.fractionate_input(inputs, target_model=self.model_adapter.name)

        q_in = inputs['flowrate']
        temperature = inputs['temperature']
        inflow_components = self.model_adapter.dict_to_vector(inputs['components'])

        c_out = self._simulate_reactor(inflow_components, q_in, dt)

        comp_out = self.model_adapter.vector_to_dict(c_out)
        results = self.sludge_metrics.compute(comp_out, inflow_components, q_in, dt, self.volume, temperature, self.waste_ratio)

        self.metrics = {
            'cod_removal': results['cod_removal_rate'],
            'hrt': results['hrt_hours'],
            'mlss': results['tss'],
            'energy_kwh': results['aeration_energy_kwh']
        }
        self.concentrations = c_out
        self.state = comp_out
        self.outputs = results
        return results

    def _simulate_reactor(self, c_in: np.ndarray, q_in: float, dt: float) -> np.ndarray:
        """Simulation d'un CSTR (réacteur parfaitement agité)"""
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
    
    def update_state(self, outputs: Dict[str, Any]) -> None:
        """Met à jour l'état interne"""
        self.state = outputs['components'].copy()
        self.outputs = outputs
    
    def __repr__(self):
        return f"<ActivatedSludgeProcess {self.name} [{self.model_adapter.name}] V={self.volume}m^3>"
        