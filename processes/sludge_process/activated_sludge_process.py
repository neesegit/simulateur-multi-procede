"""
ActivatedSludgeProcess - Procédé générique de boues activées
"""
import numpy as np
import logging

from typing import Dict, Any, List

from core.process.process_node import ProcessNode
from processes.sludge_process.sludge_metrics import SludgeMetrics
from processes.sludge_process.sludge_model_adapter import SludgeModelAdapter

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

        model_name = config.get('model', 'ASM1').upper()
        self.model_adapter = SludgeModelAdapter(model_name, config.get('model_parameters'))
        
        self.concentrations = np.zeros(self.model_adapter.size)
        self.sludge_metrics = SludgeMetrics(model_name)
        self.logger.info(f"{self} initialisé")
    
    def initialize(self) -> None:
        """Initialise l'état du bassin"""
        init_state = self.model_adapter.initial_state(do_setpoint=self.do_setpoint)
        self.concentrations = self.model_adapter.dict_to_vector(init_state)
        self.state = init_state

    def get_required_inputs(self) -> List[str]:
        return ['flow', 'flowrate', 'temperature']
    
    def process(self, inputs: Dict[str, Any], dt: float) -> Dict[str, Any]:
        """Exécute un pas de simulation pour le procédé"""
        inputs = self.fractionate_input(inputs, target_model=self.model_adapter.name)

        q_in = inputs['flowrate']
        inflow_components = self.model_adapter.dict_to_vector(inputs['components'])

        c_out = self._simulate_reactor(inflow_components, q_in, dt)

        comp_out = self.model_adapter.vector_to_dict(c_out)
        results = self.sludge_metrics.compute(comp_out, inflow_components, q_in, dt, self.volume)

        self.metrics = {
            'cod_removal': results['cod_removal_rate'],
            'hrt': results['hrt_hours'],
            'mlss': results['ss'],
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

        for _ in range(max(1, int(dt_day / 0.01))):
            dc_dt = dilution * (c_in - c) + self.model_adapter.reactions(c)
            c += dc_dt * (dt_day / max(1, int(dt_day / 0.01)))
            c = np.maximum(c, 1e-10)
            self.model_adapter.enforce_oxygen_setpoint(c, self.do_setpoint)
        return c
    
    def update_state(self, outputs: Dict[str, Any]) -> None:
        """Met à jour l'état interne"""
        self.state = outputs['components'].copy()
        self.outputs = outputs
    
    def __repr__(self):
        return f"<ActivatedSludgeProcess {self.name} [{self.model_adapter.name}] V={self.volume}m^3>"
        