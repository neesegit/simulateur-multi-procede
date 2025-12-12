import logging

from datetime import datetime
from typing import Dict, Any, List, Tuple

from core.data.databuses import DataBus
from core.data.simulation_flow import SimulationFlow
from core.process.process_node import ProcessNode
from core.orchestrator.orchestrator_state import OrchestratorState
from core.orchestrator.result_manager import ResultManager
from core.orchestrator.influent_initializer import InfluentInitializer
from core.connection.connection_manager import ConnectionManager
from core.connection.connection import Connection

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

        self.connection_manager = ConnectionManager()

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
        self._setup_connections()
        for process in self.process_nodes:
            process.initialize()
        influent = InfluentInitializer.create_from_config(self.config, self.state.current_time)
        self.databus.write_flow('influent', influent)
        self.simulation_flow.add_flow('influent', influent)
        self.logger.info("Simulation initialisée")

    def _setup_connections(self) -> None:
        """Configure le gestaionnaire de connexions depuis la config"""
        connections_config = self.config.get('connections', {})

        if not connections_config:
            self.logger.warning("Aucune connexion définie, création d'une chaîne séquentielle")
            self._create_sequential_connections()
            return
        
        for conn in connections_config:
            self.connection_manager.add_connection(
                source_id=conn['source'],
                target_id=conn['target'],
                flow_fraction=conn.get('fraction', 1.0),
                is_recycle=conn.get('is_recycle', False)
            )
        
        validation = self.connection_manager.validate()
        if validation['errors']:
            for error in validation['errors']:
                self.logger.error(error)
            raise ValueError("Erreurs dans le graphe de connexions")
        
        if validation['warnings']:
            for warning in validation['warnings']:
                self.logger.warning(warning)

        self.logger.info("\n"+self.connection_manager.visualize_ascii())
   
    def _create_sequential_connections(self) -> None:
        """Crée une chaîne séquentielle simple"""
        if not self.process_nodes:
            return
        
        first = self.process_nodes[0]
        self.connection_manager.add_connection('influent', first.node_id, 1.0, False)

        for i in range(len(self.process_nodes) - 1):
            current = self.process_nodes[i]
            next_proc = self.process_nodes[i+1]
            self.connection_manager.add_connection(
                current.node_id,
                next_proc.node_id,
                1.0,
                False
            )

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
            'sim_name': self.config.get('name', 'simulation'),
            'start_time': str(self.state.start_time),
            'end_time': str(self.state.end_time),
            'total_hours': (self.state.end_time - self.state.start_time).total_seconds()/3600,
            'timestep': self.state.timestep,
            'steps_completed': self.state.current_step
        }
        return self.result_manager.collect(metadata)

    def _run_timestep(self) -> None:
        """
        Exécute un seul pas de temps de simulation
        """
        execution_order = self.connection_manager.get_execution_order()

        for node_id in execution_order:
            if node_id == 'influent':
                continue

            process = self.process_map.get(node_id)
            if not process:
                continue

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
        upstream_connections = self.connection_manager.get_upstream_nodes(process.node_id)

        if not upstream_connections:
            self.logger.warning(f"Aucun upstream pour {process.node_id}")
            return {}
        
        if len(upstream_connections) == 1:
            source_id, connection = upstream_connections[0]
            source_flow = self.databus.read_flow(source_id)

            if not source_flow:
                self.logger.warning(f"Flux manquant pour {source_id}")
                return {}
            
            fraction = connection.flow_fraction
            return {
                'flow': source_flow,
                'flowrate': source_flow.flowrate * fraction,
                'temperature': source_flow.temperature,
                'components': source_flow.components.copy()
            } 
        return self._mix_multiple_sources(upstream_connections)
    
    def _mix_multiple_sources(self, upstream_connections: List[Tuple[str, Connection]]) -> Dict[str, Any]:
        """
        Mélange plusiseurs flux sources avec leurs fractions respectives
        """
        total_flowrate = 0.0
        weighted_temp = 0.0
        weighted_components: Dict[str, float] = {}

        reference_flow = None

        for source_id, connection in upstream_connections:
            source_flow = self.databus.read_flow(source_id)

            if not source_flow:
                self.logger.warning(f"Flux manquant pour {source_id}")
                continue

            if reference_flow is None:
                reference_flow = source_flow

            fractional_flowrate = source_flow.flowrate * connection.flow_fraction
            total_flowrate += fractional_flowrate

            weighted_temp += source_flow.temperature * fractional_flowrate

            for component, concentration in source_flow.components.items():
                if component not in weighted_components:
                    weighted_components[component] = 0.0
                weighted_components[component] += concentration * fractional_flowrate

        if total_flowrate == 0:
            self.logger.error("Débit total nul après mélange")
            return {}
        
        mixed_temperature = weighted_temp / total_flowrate
        mixed_components = {
            comp: value / total_flowrate
            for comp, value in weighted_components.items()
        }

        return {
            'flow': reference_flow,
            'flowrate': total_flowrate,
            'temperature': mixed_temperature,
            'components': mixed_components
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

        metrics_to_store = [
            'cod_soluble', 'cod_particulate', 'soluble_cod_removal',
            'cod_removal_rate', 'hrt_hours', 'srt_days', 'svi',
            'biomass_concentration', 'oxygen_consumed_kg',
            'aeration_energy_kwh', 'energy_per_m3'
        ]

        for metric in metrics_to_store:
            if metric in outputs:
                flow.components[metric] = outputs[metric]


        for key in ['cod', 'ss', 'bod', 'tkn', 'nh4', 'no3', 'po4']:
            if key in outputs:
                value = outputs[key]
                setattr(flow, key, value)
                if key not in flow.components:
                    flow.components[key] = value
        return flow