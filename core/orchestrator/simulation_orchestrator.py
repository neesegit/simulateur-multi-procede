import logging

from datetime import datetime
from typing import Dict, Any, List, Optional
from core.databuses import DataBus
from core.simulation_flow import SimulationFlow
from core.process_node import ProcessNode
from core.orchestrator.orchestrator_state import OrchestratorState
from core.orchestrator.result_manager import ResultManager
from core.orchestrator.influent_initializer import InfluentInitializer

class SimulationOrchestrator:
    """Cerveau du simulateur - coordination entre procédés et flux"""

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        sim_config = config.get('simulation', {})
        self.logger = logging.getLogger(f"{__name__}.{config.get('name','sim')}")

        self.state = OrchestratorState(
            start_time=datetime.fromisoformat(sim_config.get('start_time')),
            end_time=datetime.fromisoformat(sim_config.get('end_time')),
            timestep_hours=sim_config.get('timestep_hours', 0.1)
        )
        self.databus = DataBus()
        self.simulation_flow = SimulationFlow()
        self.result_manager = ResultManager(self.simulation_flow)

        self.process_nodes: List[ProcessNode] = []
        self.process_map: Dict[str, ProcessNode] = {}
        self.is_running = False

    def add_process(self, process: ProcessNode) -> None:
        """
        Ajoute un ProcessNode à la chaîne de simulation

        Args:
            process (ProcessNode): Instance de ProcessNode à ajouter
        """
        if process.node_id in self.process_map:
            raise ValueError(f"Duplicate ProcessNode ID '{process.node_id}'")
        self.process_nodes.append(process)
        self.process_map[process.node_id] = process
        self.logger.info(f"ProcessNode ajouté : {process.name}")

    def initialize(self) -> None:
        """
        Initialise tous les processNodes et prépare la simulation
        """
        self.logger.info("Initialisation de la simulation ...")
        for process in self.process_nodes:
            process.initialize()
        influent = InfluentInitializer.create_from_config(self.config, self.state.current_time)
        self.databus.write_flow('influent', influent)
        self.simulation_flow.add_flow('influent', influent)
        self.logger.info("Simulation initialisée")

    def run(self) -> Dict[str, Any]:
        """
        Exécute la simulation complète

        Returns:
            Dict[str, Any]: Dictionnaire contenant les résultats de la simulation
        """
        self.is_running = True
        total_steps = self.state.total_steps
        self.logger.info(f"Simulation : {total_steps} pas de temps")

        while self.state.current_time < self.state.end_time:
            self._run_timestep()
            self.state.advance()
            if self.state.current_step % 100 == 0:
                self.logger.info(f"{self.state.progress_percent():.1f}% complété")
        self.is_running = False
        metadata = {
            'start_time': str(self.state.start_time),
            'end_time': str(self.state.end_time),
            'timestep': self.state.timestep,
            'steps_completed': self.state.current_step
        }
        return self.result_manager.collect(metadata)

    def _run_timestep(self) -> None:
        """
        Exécute un seul pas de temps de simulation
        """
        for process in self.process_nodes:
            inputs = self._get_process_inputs(process)
            outputs = process.process(inputs, dt=self.state.timestep)
            process.update_state(outputs)
            flow = self._create_output_flow(process, outputs)
            self.databus.write_flow(process.node_id, flow)
            self.simulation_flow.add_flow(process.node_id, flow)

    def _get_process_inputs(self, process: ProcessNode) -> Dict[str, Any]:
        """
        Récupère les inputs pour un ProcessNode depuis le DataBus

        Args:
            process (ProcessNode): ProcessNode dont on veut les inputs

        Returns:
            Dict[str, Any]: Dictionnaire des inputs
        """
        upstream_id = process.upstream_nodes[0] if process.upstream_nodes else 'influent'
        upstream_flow = self.databus.read_flow(upstream_id)
        if not upstream_flow:
            return {}
        return {
            'flow': upstream_flow,
            'flowrate': upstream_flow.flowrate,
            'temperature': upstream_flow.temperature,
            'components': upstream_flow.components.copy()
        }

    def _create_output_flow(self, process: ProcessNode, outputs: Dict[str, Any]):
        """
        Crée un FlowData à partir des outputs d'un ProcessNode

        Args:
            process (ProcessNode): ProcessNode source
            outputs (Dict[str, Any]): Dictionnaire des outputs

        Returns:
            FlowData: FlowData contruit
        """
        from core.data.flow_data import FlowData
        flow = FlowData(
            timestamp=self.state.current_time,
            flowrate=outputs.get('flowrate', 0.0),
            temperature=outputs.get('temperature', 20.0),
            model_type=outputs.get('model_type'),
            source_node=process.node_id
        )
        flow.components = outputs.get('components', {}).copy()
        for key in ['cod', 'ss', 'bod', 'tkn']:
            if key in outputs:
                setattr(flow, key, outputs[key])
        return flow