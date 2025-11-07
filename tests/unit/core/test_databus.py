"""Tests unitaires pour DataBus et SimulationFlow"""
import pytest

from datetime import datetime, timedelta

from core.data.databuses import DataBus
from core.data.simulation_flow import SimulationFlow
from core.data.flow_data import FlowData

@pytest.mark.unit
class TestDataBus:
    """Tests du DataBus"""

    def test_initialization(self):
        """Vérifie l'initialisation"""
        bus = DataBus()
        assert bus is not None
        assert hasattr(bus, '_data_store')
        assert hasattr(bus, '_flow_store')

    def test_write_read_data(self, databus):
        """Vérifie l'écriture et lecture de données simples"""
        databus.write('test_key', 42)
        value = databus.read('test_key')
        assert value == 42

    def test_read_nonexistent_key(self, databus):
        """Vérifie la valeur par défaut"""
        value = databus.read('nonexistent')
        assert value is None

    def test_read_with_default(self, databus):
        """Vérifie la valeur par défaut"""
        value = databus.read('nonexistent', default=100)
        assert value == 100

    def test_write_read_flow(self, databus, sample_flow_data):
        """Vérifie l'écriture et lecture de flux"""
        databus.write_flow('node1', sample_flow_data)
        retrieved = databus.read_flow('node1')

        assert retrieved is not None
        assert retrieved.flowrate == sample_flow_data.flowrate
        assert retrieved.source_node == 'node1'

    def test_read_nonexistant_flow(self, databus):
        """Vérifie la lecture d'un flux inexistant"""
        flow = databus.read_flow('nonexistent')
        assert flow is None

    def test_get_all_flows(self, databus, sample_flow_data):
        """Vérifie la récupération de tous les flux"""
        flow1 = sample_flow_data
        flow2 = FlowData(
            timestamp=datetime.now(),
            flowrate=500.0,
            temperature=25.0
        )

        databus.write_flow('node1', flow1)
        databus.write_flow('node2', flow2)

        all_flows = databus.get_all_flows()

        assert len(all_flows) == 2
        assert 'node1' in all_flows
        assert 'node2' in all_flows

    def test_clear(self, databus, sample_flow_data):
        """Vérifie le nettoyage du bus"""
        databus.write('key', 'value')
        databus.write_flow('node', sample_flow_data)

        databus.clear()

        assert databus.read('key') is None
        assert databus.read_flow('node') is None

    def test_overwrite_data(self, databus):
        """Vérifie l'écrasement de données"""
        databus.write('key', 'old_value')
        databus.wrtie('key', 'new_value')

        assert databus.read('key') == 'new_value'

    def test_multiple_writes_flows(self, databus, sample_flow_data):
        """Vérifie l'écrasement de flux (le dernier gagne)"""
        flow1 = sample_flow_data
        flow2 = FlowData(
            timestamp=datetime.now(),
            flowrate=999.0,
            temperature=30.0
        )

        databus.write_flow('node', flow1)
        databus.write_flow('node', flow2)

        retrieved = databus.read_flow('node')
        assert retrieved.flowrate == 999.0

@pytest.mark.unit
class TestSimulationFlow:
    """Tests de SimulationFlow"""

    def test_initialization(self):
        """Vérifie l'initialisation"""
        flow = SimulationFlow()
        assert flow is not None
        assert hasattr(flow, '_history')

    def test_add_flow(self, simulation_flow, sample_flow_data):
        """Vérifie l'ajout d'un flux"""
        simulation_flow.add_flow('node1', sample_flow_data)

        history = simulation_flow.get_history('node1')
        assert len(history) == 1
        assert history[0].flowrate == sample_flow_data.flowrate

    def test_add_multiple_flows(self, simulation_flow, sample_timestamp):
        """Vérifie l'ajout de plusieurs flux"""
        for i in range(5):
            flow = FlowData(
                timestamp=sample_timestamp + timedelta(hours=i),
                flowrate=1000.0 + i * 10,
                temperature=20.0
            )
            simulation_flow.add_flow('node1', flow)
        
        history = simulation_flow.get_history('node1')
        assert len(history) == 5
        assert history[4]. flowrate == 1040.0

    def test_get_history_nonexistent(self, simulation_flow):
        """Vérifie l'historique d'un noeud inexistant"""
        history = simulation_flow.get_history('nonexistent')
        assert history == []

    def test_get_latest(self, simulation_flow, sample_timestamp):
        """Vérifie la récupération du dernier flux"""
        for i in range(3):
            flow = FlowData(
                timestamp=sample_timestamp + timedelta(hours=i),
                flowrate=1000.0 + i * 100,
                temperature=20.0
            )
            simulation_flow.add_flow('node1', flow)
        latest = simulation_flow.get_latest('node1')
        assert latest is not None
        assert latest.flowrate == 1200.0

    def test_get_latest_empty(self, simulation_flow):
        """Vérifie get_latest sur un noeud vide"""
        latest = simulation_flow.get_latest('empty_node')
        assert latest is None

    def test_get_all_histories(self, simulation_flow, sample_flow_data):
        simulation_flow.add_flow('node1', sample_flow_data)
        simulation_flow.add_flow('node2', sample_flow_data)

        all_histories = simulation_flow.get_all_histories()

        assert len(all_histories) == 2
        assert 'node1' in all_histories
        assert 'node2' in all_histories

    def test_clear(self, simulation_flow, sample_flow_data):
        """Vérifie le nettoyage"""
        simulation_flow.add_flow('node1', sample_flow_data)
        simulation_flow.clear()

        history = simulation_flow.get_history('node1')
        assert history == []

    def test_export_to_dict(self, simulation_flow, sample_timestamp):
        """Vérifie l'export en dictionnaire"""
        for i in range(2):
            flow = FlowData(
                timestamp=sample_timestamp + timedelta(hours=i),
                flowrate=1000.0,
                temperature=20.0
            )
            simulation_flow.add_flow('node1', flow)
        
        exported = simulation_flow.export_to_dict()

        assert isinstance(exported, dict)
        assert 'node1' in exported
        assert len(exported['node1']) == 2
        assert isinstance(exported['node1'][0], dict)

    def test_chronological_order(self, simulation_flow, sample_timestamp):
        """Vérifie que l'ordre chronologique est préservé"""
        times = []
        for i in range(5):
            t = sample_timestamp + timedelta(hours=i)
            times.append(t)
            flow = FlowData(timestamp=t, flowrate=1000.0, temperature=20.0)
            simulation_flow.add_flow('node1', flow)
        
        history = simulation_flow.get_history('node1')

        for i, flow in enumerate(history):
            assert flow.timestamp == times[i]

@pytest.mark.unit
class TestFlowData:
    """Tests de FlowData"""

    def test_initialization(self, sample_timestamp):
        """Vérifie l'initialisation"""
        flow = FlowData(
            timestamp=sample_timestamp,
            flowrate=1000.0,
            temperature=20.0
        )

        assert flow.timestamp == sample_timestamp
        assert flow.flowrate == 1000.0
        assert flow.temperature == 20.0

    def test_get_standard_component(self, sample_flow_data):
        """Vérifie l'accès aux composants standards"""
        assert sample_flow_data.get('cod') == 500.0
        assert sample_flow_data.get('ss') == 250.0

    def test_get_nonexistent_component(self, sample_flow_data):
        """Vérifie l'accès à un composant inexistant"""
        assert sample_flow_data.get('nonexistent') == 0.0
        assert sample_flow_data.get('nonexistent', 99.0) == 99.0

    def test_set_component(self, sample_flow_data):
        """Vérifie la modification d'un composant"""
        sample_flow_data.set('cod', 600.0)
        assert sample_flow_data.get('cod') == 600.0

    def test_set_custom_component(self, sample_flow_data):
        """Vérifie l'ajout d'un composant personnalisé"""
        sample_flow_data.set('custom_param', 123.45)
        assert sample_flow_data.get('custom_param') == 123.45

    def test_has_model_components(self, sample_flow_data):
        """Vérifie la détection de composants de modèle"""
        assert not sample_flow_data.has_model_components()

        sample_flow_data.components['si'] = 30.0
        assert sample_flow_data.has_model_components()

    def test_get_all_components(self, sample_flow_data):
        """Vérifie la récupération de tous les composants"""
        sample_flow_data.set('custom', 100.0)

        all_comp = sample_flow_data.get_all_components()

        assert 'cod' in all_comp
        assert 'custom' in all_comp

    def test_extract_measured(self, sample_flow_data):
        """Vérifie l'extraction des paramètres mesurés"""
        measured = sample_flow_data.extract_measured()

        assert 'cod' in measured
        assert 'ss' in measured
        assert measured['cod'] == 500.0

    def test_to_dict(self, sample_flow_data):
        """Vérifie la conversion en dictionnaire"""
        data_dict = sample_flow_data.to_dict()

        assert isinstance(data_dict, dict)
        assert 'timestamp' in data_dict
        assert 'flowrate' in data_dict

    def test_copy(self, sample_flow_data):
        """Vérifie la copie"""
        copy = sample_flow_data.copy()

        assert copy.flowrate == sample_flow_data.flowrate
        assert copy.timestamp == sample_flow_data.timestamp

        copy.flowrate = 2000.0
        assert sample_flow_data == 1000.0