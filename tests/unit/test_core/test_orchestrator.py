"""
Tests de l'orchestrateur
"""
import pytest
from unittest.mock import Mock, MagicMock, patch, call
from datetime import datetime, timedelta

from core.orchestrator.simulation_orchestrator import SimulationOrchestrator
from core.connection.connection_manager import ConnectionManager
from core.process.process_factory import ProcessFactory

class TestSimulationOrchestrator:
    """Tests SimulationOrchestrator"""

    @patch('core.orchestrator.simulation_orchestrator.DataBus')
    def test_initialization_creates_components(self, MockDataBus):
        """Test : initialisation crée les composants"""
        config = {
            'name': 'test_sim',
            'simulation': {
                'start_time': '2025-12-11T00:00:00',
                'end_time': '2025-12-11T01:00:00',
                'timestep_hours': 0.1
            },
            'influent': {'flowrate': 1000.0, 'temperature': 20.0},
            'processes': []
        }

        orchestrator = SimulationOrchestrator(config)

        assert orchestrator.databus is not None
        assert orchestrator.simulation_flow is not None
        assert orchestrator.state is not None

    def test_add_process_registers_node(self):
        """Test : add_process enregistre le noeud"""
        config = {
            'name': 'test',
            'simulation': {
                'start_time': '2025-12-11T00:00:00',
                'end_time': '2025-12-11T01:00:00',
                'timestep_hours': 0.1
            },
            'influent': {'flowrate': 1000.0, 'temperature': 20.0},
            'processes': []
        }

        orchestrator = SimulationOrchestrator(config)

        mock_process = MagicMock()
        mock_process.node_id = 'proc1'
        mock_process.name = 'process 1'

        orchestrator.add_process(mock_process)

        assert 'proc1' in orchestrator.process_map
        assert len(orchestrator.process_nodes) == 1

    def test_add_duplicate_process_raises_error(self):
        """Test : ajout process dupliqué lève une erreur"""
        config = {
            'name': 'test',
            'simulation': {
                'start_time': '2025-12-11T00:00:00',
                'end_time': '2025-12-11T01:00:00',
                'timestep_hours': 0.1
            },
            'influent': {'flowrate': 1000.0, 'temperature': 20.0},
            'processes': []
        }

        orchestrator = SimulationOrchestrator(config)

        mock_process1 = MagicMock()
        mock_process1.node_id = 'proc1'

        mock_process2 = MagicMock()
        mock_process2.node_id = 'proc1'

        orchestrator.add_process(mock_process1)

        with pytest.raises(ValueError, match="Duplicate"):
            orchestrator.add_process(mock_process2)

    @patch('core.orchestrator.simulation_orchestrator.InfluentInitializer')
    def test_initialize_creates_influent(self, MockInfluent):
        """Test : initialize crée l'influent"""
        config = {
            'name': 'test',
            'simulation': {
                'start_time': '2025-12-11T00:00:00',
                'end_time': '2025-12-11T01:00:00',
                'timestep_hours': 0.1
            },
            'influent': {'flowrate': 1000.0, 'temperature': 20.0},
            'processes': []
        }

        mock_flow = MagicMock()
        MockInfluent.create_from_config.return_value = mock_flow

        orchestrator = SimulationOrchestrator(config)

        mock_process = MagicMock()
        mock_process.node_id = 'proc1'
        orchestrator.add_process(mock_process)

        orchestrator.initialize()

        MockInfluent.create_from_config.assert_called_once()
        mock_process.initialize.assert_called_once()

    def test_run_timestep_calls_processes(self):
        """Test : _run_timestep appelle tous les processus"""
        config = {
            'name': 'test',
            'simulation': {
                'start_time': '2025-12-11T00:00:00',
                'end_time': '2025-12-11T01:00:00',
                'timestep_hours': 0.1
            },
            'influent': {'flowrate': 1000.0, 'temperature': 20.0},
            'processes': [],
            'connections': []
        }

        orchestrator = SimulationOrchestrator(config)

        mock_proc1 = MagicMock()
        mock_proc1.node_id = 'proc1'
        mock_proc1.process.return_value = {'flowrate': 1000.0}
        mock_proc1.update_state = MagicMock()

        orchestrator.add_process(mock_proc1)

        orchestrator.connection_manager.add_connection('influent', 'proc1', 1.0, False)

        mock_flow = MagicMock()
        mock_flow.flowrate = 1000.0
        mock_flow.temperature = 20.0
        mock_flow.components = {}

        orchestrator.databus.write_flow('influent', mock_flow)
        orchestrator.initialize()

        orchestrator._run_timestep()

        assert mock_proc1.process.call_count == 1


    @patch('core.orchestrator.simulation_orchestrator.InfluentInitializer')
    def test_run_advances_time(self, MockInfluent):
        """Test : run avance le temps"""
        config = {
            'name': 'test',
            'simulation': {
                'start_time': '2025-12-11T00:00:00',
                'end_time': '2025-12-11T00:10:00',
                'timestep_hours': 0.1
            },
            'influent': {'flowrate': 1000.0, 'temperature': 20.0},
            'processes': [],
            'connections': []
        }

        MockInfluent.create_from_config.return_value = MagicMock()

        orchestrator = SimulationOrchestrator(config)
        orchestrator.initialize()

        initial_time = orchestrator.state.current_time

        with patch.object(orchestrator, '_run_timestep'):
            orchestrator.run()

        assert orchestrator.state.current_time > initial_time

class TestConnectionManager:
    """Tests ConnectionManager"""

    def test_add_connection_validates_fraction(self):
        """Test : add_connection valide la fraction"""
        manager = ConnectionManager()

        with pytest.raises(ValueError, match='flow_fraction'):
            manager.add_connection('source', 'target', flow_fraction=1.5)

        with pytest.raises(ValueError, match='flow_fraction'):
            manager.add_connection('source', 'target', flow_fraction=0.0)

    def test_add_connection_rejects_self_loop(self):
        """Test : rejette les boucles sur soi-même"""
        manager = ConnectionManager()

        with pytest.raises(ValueError, match='différents'):
            manager.add_connection('node1', 'node1')

    @patch('core.connection.connection_manager.logger')
    def test_add_connection_logs(self, mock_logger):
        """Test : add_conenction log l'ajout"""
        manager = ConnectionManager()

        manager.add_connection('source', 'target', 1.0, False)

        mock_logger.debug.assert_called()

    def test_get_upstream_nodes(self):
        """Test : get_upstream_nodes retourne les sources"""
        manager = ConnectionManager()

        manager.add_connection('source1', 'target', 0.5)
        manager.add_connection('source2', 'target', 0.5)

        upstream = manager.get_upstream_nodes('target')

        assert len(upstream) == 2
        source_ids = [s for s, _ in upstream]
        assert 'source1' in source_ids
        assert 'source2' in source_ids

    def test_validate_detects_fraction_overflow(self):
        """Test : validate détecte les fractions > 1"""
        manager = ConnectionManager()

        manager.add_connection('source', 'target1', 0.6)
        manager.add_connection('source', 'target2', 0.5)

        validation = manager.validate()

        assert len(validation['errors']) > 0
        assert any('fraction' in err for err in validation['errors'])

class TestProcessFactory:
    """Tests ProcessFactory"""

    @patch('core.process.process_factory.ProcessRegistry')
    def test_create_process_uses_registry(self, MockRegistry):
        """Test : create_process utilise le registre"""
        mock_registry = MagicMock()
        MockRegistry.get_instance.return_value = mock_registry

        mock_process = MagicMock()
        mock_registry.create_process.return_value = mock_process

        config = {
            'node_id': 'proc1',
            'type': 'ActivatedSludgeProcess',
            'name': 'process1',
            'config': {}
        }

        process = ProcessFactory.create_process(config)

        mock_registry.create_process.assert_called_once_with(
            process_type='ActivatedSludgeProcess',
            node_id='proc1',
            name='process1',
            config={}
        )
        assert process is mock_process

    @patch('core.process.process_factory.ConnectionManager')
    @patch('core.process.process_factory.ProcessRegistry')
    def test_setup_connections_called(self, MockRegistry, MockConnManager):
        """Test : _setup_connections est appelé"""
        mock_registry = MagicMock()
        MockRegistry.get_instance.return_value = mock_registry

        mock_process = MagicMock()
        mock_process.node_id = 'proc1'
        mock_registry.create_process.return_value = mock_process

        mock_conn_manager = MagicMock()
        MockConnManager.return_value = mock_conn_manager

        config = {
            'processes': [
                {
                    'node_id': 'proc1',
                    'type': 'ActivatedSludgeProcess',
                    'name': 'p1'
                }
            ],
            'conncetions': [
                {
                    'source': 'influent',
                    'target': 'proc1',
                    'fraction': 1.0,
                    'is_recycle': False
                }
            ]
        }

        with patch.object(ProcessFactory, '_setup_connections') as mock_setup:
            processes = ProcessFactory.create_from_config(config)

            mock_setup.assert_called_once()