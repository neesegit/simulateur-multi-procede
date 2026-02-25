"""SecondarySettlerProcess - Procédé de décantation secondaire"""
import numpy as np
import logging

from typing import Dict, Any, List
from core.process.process_node import ProcessNode
from core.model.model_registry import ModelRegistry
from core.context.settler_context import SettlerContext
from core.solver.settler_solver import SettlerSolver

logger = logging.getLogger(__name__)

class SecondarySettlerProcess(ProcessNode):
    """
    Procédé de décantation secondaire (clarificateur)
    """

    def __init__(self, node_id: str, name: str, config: Dict[str, Any]) -> None:
        """
        Initialise le décanteur secondaire

        Args:
            node_id (str): Identifiant unique
            name (str): Nom du procédé
            config (Dict[str, Any]): Configuration contenant :
                - area : Surface du décanteur (m²)
                - depth : Profondeur totale (m)
                - n_layers : Nombre de couches
                - underflow_ratio : Ratio Qunderflow / Qin
                - feed_layer_ratio : Position relative d'alimentation (0-1)
                - model : Type de modèle
                - model_parameters : Paramètres du modèle
        """
        super().__init__(node_id, name, config)

        self.area = config.get('area', 1000.0)
        self.depth = config.get('depth', 4.0)
        self.n_layers = config.get('n_layers', 10)
        self.layer_height = self.depth / self.n_layers

        self.underflow_ratio = config.get('underflow_ratio', 0.5)
        feed_layer_ratio = config.get('feed_layer_ratio', 0.5)
        self.feed_layer = int(self.n_layers * (1 - feed_layer_ratio))

        model_type = config.get('model', 'TakacsModel')
        model_params = config.get('model_parameters', {})
        model_params['n_layers'] = self.n_layers

        registry = ModelRegistry.get_instance()

        try:
            self.model_instance = registry.create_model(
                model_type=model_type,
                params=model_params
            )
            self.model_type = model_type
            logger.info(f'Modèle chargé : {model_type}')
        except ValueError as e:
            logger.error(f"Erreur de chargement du modèle : {e}")
            raise

        self.concentrations = np.zeros(self.n_layers)

        self.sludge_blanket_info = {}

        logger.info(
            f"{self} initialisé - {self.n_layers} couches, "
            f"surface={self.area}m², profondeur={self.depth}m"
        )

    def initialize(self) -> None:
        """Initialise l'état du décanteur"""
        initial_concentration = 500.0
        self.concentrations = np.full(self.n_layers, initial_concentration)

        for i in range(self.n_layers):
            depth_factor = i / self.n_layers
            self.concentrations[i] = initial_concentration * (1 + 2*depth_factor)

        self.state = {
            f'layer_{i}': self.concentrations[i]
            for i in range(self.n_layers)
        }

        logger.info("Décanteur initialisé avec profil de concentration initial")

    def get_required_inputs(self) -> List[str]:
        return ['flow', 'flowrate', 'temperature', 'components']
    
    def process(self, inputs: Dict[str, Any], dt: float) -> Dict[str, Any]:
        """
        Exécute un pas de simulation pour le décanteur

        Args:
            inputs (Dict[str, Any]): Données d'entrée
            dt (float): Pas de temps (h)

        Returns:
            Dict[str, Any]: Sorties du décanteur
        """
        Q_in = inputs['flowrate']
        temperature = inputs['temperature']

        flow = inputs.get('flow')
        if flow:
            X_in = flow.tss if flow.tss > 0 else flow.get('mlss', 2000.0)
        else:
            components = inputs.get('components', {})
            X_in = components.get('tss', components.get('mlss', 2000.0))

        Q_underflow = Q_in * self.underflow_ratio
        Q_overflow = Q_in - Q_underflow

        context = SettlerContext(
            model=self.model_instance,
            Q_in=Q_in,
            Q_underflow=Q_underflow,
            Q_overflow=Q_overflow,
            X_in=X_in,
            area=self.area,
            layer_height=self.layer_height,
            feed_layer=self.feed_layer,
            X_min=0.0,
            X_max=15000.0
        )

        X_next = SettlerSolver.solve_step(
            X=self.concentrations,
            context=context,
            dt=dt,
            method='rk4'
        )

        effluent = SettlerSolver.compute_effluent_quality(X_next, context)

        self.sludge_blanket_info = SettlerSolver.detect_sludge_blanket(X_next)

        self.concentrations = X_next

        results = self._prepare_outputs(
            effluent, X_in, Q_in, Q_overflow, Q_underflow,
            temperature, inputs
        )

        self.metrics = {
            'removal_efficiency': effluent['removal_efficiency'],
            'X_overflow': effluent['X_overflow'],
            'X_underflow': effluent['X_underflow'],
            'has_sludge_blanket': self.sludge_blanket_info.get('has_blanket', False)
        }

        self.outputs = results
        return results
    
    def _prepare_outputs(
            self,
            effluent: Dict,
            X_in: float,
            Q_in: float,
            Q_overflow: float,
            Q_underflow: float,
            temperature: float,
            inputs: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Prépare les sorties du décanteur"""
        components_overflow = {}
        components_underflow = {}

        input_components = inputs.get('components', {})

        fraction_overflow = effluent['X_overflow'] / X_in if X_in > 0 else 0.1
        fraction_underflow = effluent['X_underflow'] / X_in if X_in > 0 else 2.0

        for comp, value in input_components.items():
            if comp.startswith('s'):
                components_overflow[comp] = value * 0.95
                components_underflow[comp] = value * 0.05
            elif comp.startswith('x'):
                components_overflow[comp] = value * fraction_overflow
                components_underflow[comp] = value * fraction_underflow
            else:
                components_overflow[comp] = value
                components_underflow[comp] = value

        # Métriques de qualité de l'effluent (overflow)
        input_flow = inputs.get('flow')
        if input_flow:
            nh4 = getattr(input_flow, 'nh4', components_overflow.get('snh', 0.0))
            no3 = getattr(input_flow, 'no3', components_overflow.get('sno', 0.0))
            tkn = getattr(input_flow, 'tkn', 0.0)
            input_cod = getattr(input_flow, 'cod', 0.0)
            if input_cod > 0:
                cod_soluble = input_flow.components.get('cod_soluble', 0.0)
                cod_particulate = max(0.0, input_cod - cod_soluble)
                cod = cod_soluble + cod_particulate * fraction_overflow
            else:
                cod = 0.0
        else:
            nh4 = components_overflow.get('snh', 0.0)
            no3 = components_overflow.get('sno', 0.0)
            tkn = (components_overflow.get('snh', 0.0)
                   + components_overflow.get('snd', 0.0)
                   + components_overflow.get('xnd', 0.0))
            cod = 0.0

        results = {
            'flowrate': Q_overflow,
            'temperature': temperature,
            'model_type': self.model_type,
            'tss': effluent['X_overflow'],
            'cod': cod,
            'nh4': nh4,
            'no3': no3,
            'tkn': tkn,
            'components': components_overflow,

            'underflow': {
                'flowrate': Q_underflow,
                'tss': effluent['X_underflow'],
                'components': components_underflow
            },

            'X_overflow': effluent['X_overflow'],
            'X_underflow': effluent['X_underflow'],
            'removal_efficiency': effluent['removal_efficiency'],
            'mass_overflow_kg_h': effluent['mass_overflow_kg_h'],
            'mass_underflow_kg_h': effluent['mass_underflow_kg_h'],

            'sludge_blanket': self.sludge_blanket_info,
            'layer_concentrations': self.concentrations.tolist(),
            'feed_layer': self.feed_layer,
            'layer_height': self.layer_height,

            'overflow_rate': Q_overflow / self.area,
            'underflow_rate': Q_underflow / self.area,
            'surface_loading': Q_in / self.area,
            'solids_loading': (Q_in * X_in / 1000) / self.area
        }

        return results
    
    def update_state(self, outputs: Dict[str, Any]) -> None:
        """Met à jour l'état interne"""
        self.state = {
            f'layer_{i}': self.concentrations[i]
            for i in range(self.n_layers)
        }
        self.outputs = outputs

    def __repr__(self) -> str:
        return (
            f"<SecondarySettlerProcess {self.name} "
            f"[{self.model_type}] A={self.area}m², "
            f"D={self.depth}m, layers={self.n_layers}"
        )