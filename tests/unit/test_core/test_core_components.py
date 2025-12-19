"""
Tests unitaires pour les composants core
"""
import pytest
import numpy as np

from datetime import datetime, timedelta
from unittest.mock import Mock, MagicMock

from core.data.flow_data import FlowData
from core.data.databuses import DataBus
from core.data.simulation_flow import SimulationFlow
from core.solver.ode_solver import ODESolver
from core.solver.cstr_solver import CSTRSolver

class TestFlowData:
    """Tests pour flowdata"""

    def test_basic_creation(self):
        """Test : création basique"""
        timestamp = datetime.now()
        flow = FlowData(
            timestamp=timestamp,
            flowrate=1000.0,
            temperature=20.0
        )

        assert flow.timestamp == timestamp
        assert flow.flowrate == 1000.0
        assert flow.temperature == 20.0

    def test_with_standard_params(self):
        """Test : avec paramètres standards"""
        flow = FlowData(
            timestamp=datetime.now(),
            flowrate=1000.0,
            temperature=20.0,
            tss=250.0,
            cod=500.0,
            tkn=40.0,
            nh4=28.0,
            no3=0.5,
            po4=8.0
        )

        assert flow.tkn == 250.0
        assert flow.cod == 500.0
        assert flow.tkn == 40.0

    def test_components_dict(self):
        """Test : dictionnaire de composants"""
        flow = FlowData(
            timestamp=datetime.now(),
            flowrate=1000.0,
            temperature=20.0
        )

        flow.components = {'xbh': 2500.0, 'so': 2.0}
        
        assert flow.components['xbh'] == 2500.0
        assert flow.components['so'] == 2.0

    def test_get_method(self):
        """Test : méthode get()"""
        flow = FlowData(
            timestamp=datetime.now(),
            flowrate=1000.0,
            temperature=20.0,
            cod=500.0
        )

        flow.components['xbh'] = 2500.0

        assert flow.get('cod') == 1000.0
        assert flow.get('xbh') == 2500.0
        assert flow.get('unknown', 0.0) == 0.0

    def test_set_method(self):
        """Test : méthode set()"""
        flow = FlowData(
            timestamp=datetime.now(),
            flowrate=1000.0,
            temperature=20.0
        )

        flow.set('cod', 500.0)
        assert flow.cod == 500.0

        flow.set('xbh', 2500.0)
        assert flow.components['xbh'] == 2500.0

    def test_get_all_components(self):
        """Test : récupération de tous les composants"""
        flow = FlowData(
            timestamp=datetime.now(),
            flowrate=1000.0,
            temperature=20.0,
            cod=500.0,
            tss=250.0
        )

        flow.components = {'xbh': 2500.0, 'so': 2.0}

        all_comp = flow.get_all_components()

        assert 'cod' in all_comp
        assert 'tss' in all_comp
        assert 'xbh' in all_comp
        assert 'so' in all_comp

    def test_to_dict(self):
        """Test : conversion en dictionnaire"""
        flow = FlowData(
            timestamp=datetime.now(),
            flowrate=1000.0,
            temperature=20.0,
            cod=500.0
        )

        result = flow.to_dict()

        assert isinstance(result, dict)
        assert 'flowrate' in result
        assert 'temperature' in result
        assert 'timestamp' in result

    def test_copy(self):
        """Test : copie d'un flowdata"""
        original = FlowData(
            timestamp=datetime.now(),
            flowrate=1000.0,
            temperature=20.0,
            cod=500.0
        )

        copy = original.copy()

        assert copy.flowrate == original.flowrate
        assert copy.cod == original.cod

        copy.flowrate = 2000.0
        assert original.flowrate == 1000.0

    def test_validation_negative_flowrate(self):
        """Test : flowrate négatif rejeté"""
        with pytest.raises(ValueError):
            FlowData(
                timestamp=datetime.now(),
                flowrate=-1000.0,
                temperature=20.0
            )
    
    def test_validation_extreme_temperature(self):
        """Test : température extrême (warning mais pas d'erreur)"""
        flow = FlowData(
            timestamp=datetime.now(),
            flowrate=1000.0,
            temperature=60.0
        )

        assert flow.temperature == 60.0

    def test_negative_concentrations_clamped(self):
        """Test : concentrations négatives mises à zéro"""
        flow = FlowData(
            timestamp=datetime.now(),
            flowrate=1000.0,
            temperature=20.0,
            cod=-100.0
        )

        assert flow.cod == 0.0

class TestDataBus:
    """Tests pour DataBus"""
    
    def test_creation(self):
        """Test : création du DataBus"""
        bus = DataBus()

        assert bus is not None
        assert hasattr(bus, '_data_store')
        assert hasattr(bus, '_flow_store')

    def test_write_read_data(self):
        """Test : écriture et lecture de données"""
        bus = DataBus()

        bus.write('test_key', 42)
        value = bus.read('test_key')

        assert value == 42

    def test_read_nonexistent_default(self):
        """Test : lecture clé inexistante avec défaut"""
        bus = DataBus()
        value = bus.read('nonexistent', default=0)
        
        assert value == 0

    def test_write_read_flow(self):
        """Test : écriture et lecture du flux"""
        bus = DataBus()

        flow = FlowData(
            timestamp=datetime.now(),
            flowrate=1000.0,
            temperature=20.0
        )

        bus.write_flow('node_1', flow)
        retrieved = bus.read_flow('node_1')

        assert retrieved is not None
        assert retrieved.flowrate == 1000.0
        assert retrieved.source_node == 'node_1'

    def test_read_nonexistent_flow(self):
        """Test : lecture flux inexistant"""
        bus = DataBus()

        flow = bus.read_flow('nonexistent')

        assert flow is None

    def test_get_all_flows(self):
        """Test : récupération de tous les flux"""
        bus = DataBus()

        flow1 = FlowData(datetime.now(), 1000.0, 20.0)
        flow2 = FlowData(datetime.now(), 2000.0, 25.0)

        bus.write_flow('node_1', flow1)
        bus.write_flow('node_2', flow2)

        all_flows = bus.get_all_flows()

        assert len(all_flows) == 2
        assert 'node_1' in all_flows
        assert 'node_2' in all_flows

    def test_clear(self):
        """Test : nettoyage du bus"""
        bus = DataBus()

        bus.write('key1', 'value1')
        bus.write_flow('node1', FlowData(datetime.now(), 1000.0, 20.0))

        bus.clear()

        assert bus.read('key1') is None
        assert bus.read_flow('node1') is None

class TestSimulationFlow:
    """Test pour simulationflow"""

    def test_creation(self):
        """Test : création"""
        sim_flow = SimulationFlow()

        assert sim_flow is not None
        assert hasattr(sim_flow, '_history')

    def test_add_flow(self):
        """Test : ajout de flux"""
        sim_flow = SimulationFlow()

        flow = FlowData(datetime.now(), 1000.0, 20.0)
        sim_flow.add_flow('node_1', flow)

        history = sim_flow.get_history('node_1')

        assert len(history) == 1
        assert history[0].flowrate == 1000.0

    def test_multiple_flows_same_node(self):
        """test : plusieurs flux pour un noeud"""
        sim_flow = SimulationFlow()

        for i in range(5):
            flow = FlowData(
                datetime.now() + timedelta(hours=i),
                1000.0 + i * 100,
                20.0
            )
            sim_flow.add_flow('node_1', flow)

        history = sim_flow.get_history('node_1')

        assert len(history) == 5
        assert history[0].flowrate == 1000.0
        assert history[4].flowrate == 1400.0

    def test_get_latest(self):
        """Test : récupération du dernier flux"""
        sim_flow = SimulationFlow()

        for i in range(3):
            flow = FlowData(datetime.now(), 1000.0 + i, 20.0)
            sim_flow.add_flow('node_1', flow)

        latest = sim_flow.get_latest('node_1')

        assert latest is not None
        assert latest.flowrate == 1002.0

    def test_get_all_histories(self):
        """Test : tous les historiques"""
        sim_flow = SimulationFlow()

        sim_flow.add_flow('node_1', FlowData(datetime.now(), 1000.0, 20.0))
        sim_flow.add_flow('node_2', FlowData(datetime.now(), 2000.0, 25.0))

        all_histories = sim_flow.get_all_histories()

        assert len(all_histories) == 2
        assert 'node_1' in all_histories
        assert 'node_2' in all_histories

    def test_export_to_dict(self):
        """Test : export en dictionnaire"""
        sim_flow = SimulationFlow()

        flow = FlowData(datetime.now(), 1000.0, 20.0)
        sim_flow.add_flow('node_1', flow)

        exported = sim_flow.export_to_dict()

        assert isinstance(exported, dict)
        assert 'node_1' in exported
        assert isinstance(exported['node_1'], list)

    def test_clear(self):
        """Test : nettoyage"""
        sim_flow = SimulationFlow()

        sim_flow.add_flow('node_1', FlowData(datetime.now(), 1000.0, 20.0))
        sim_flow.clear()

        history = sim_flow.get_history('node_1')
        assert len(history) == 0

class TestODESolver:
    """Tests pour ODESolver"""

    def test_euler_simple(self):
        """Test : méthode d'Euler simple"""
        c0 = np.array([1.0, 2.0, 3.0])

        def dc_dt(c):
            return np.array([0.1, 0.2, 0.3])
        
        c_next = ODESolver.euler(c0, dc_dt, dt=1.0)
        
        expected = np.array([1.1, 2.2, 3.3])
        np.testing.assert_array_almost_equal(c_next, expected)

    def test_euler_zero_dt(self):
        """Test: Euler avec dt=0"""
        c0 = np.array([1.0, 2.0])

        def dc_dt(c):
            return np.array([0.5, 0.5])
        
        c_next = ODESolver.euler(c0, dc_dt, dt=0.0)

        np.testing.assert_array_almost_equal(c_next, c0)

    def test_rk4_simple(self):
        """Test : méthode RK4"""
        c0 = np.array([1.0])

        def dc_dt(c):
            return np.array([1.0])
        
        c_next = ODESolver.rk4(c0, dc_dt, dt=1.0)

        assert c_next[0] > c0[0]

    def test_negative_concentrations_clamped(self):
        """Test : concentrations négatives mises à une valeur minimale"""
        c0 = np.array([1.0, 2.0])

        def dc_dt(c):
            return np.array([-10.0, -10.0])
        
        c_next = ODESolver.euler(c0, dc_dt, dt=1.0)

        assert np.all(c_next >= 1e-10)

class TestCSTRSolver:
    """Tests pour CSTRSolver"""

    def test_solve_step_basic(self):
        """Test : pas de résolution basique"""
        c = np.ones(5) * 100
        c_in = np.ones(5) * 50

        def reactions(c):
            return np.zeros(5)
        
        c_next = CSTRSolver.solve_step(
            c=c,
            c_in=c_in,
            reaction_func=reactions,
            dt=0.1,
            dilution_rate=1.0
        )

        assert np.all(c_next < c)

    def test_with_oxygen_control(self):
        """Test : contrôle de l'oxygène"""
        c = np.ones(10) * 100
        c[7] = 1.0
        c_in = np.ones(10) * 50

        def reactions(c):
            return np.zeros(10)
        
        c_next = CSTRSolver.solve_step(
            c=c,
            c_in=c_in,
            reaction_func=reactions,
            dt=0.1,
            dilution_rate=1.0,
            oxygen_idx=7,
            do_setpoint=2.0
        )

        assert c_next[7] == 2.0

    def test_different_methods(self):
        """Test : différentes méthodes de résolution"""
        c = np.ones(5) * 100
        c_in = np.ones(5) * 50

        def reactions(c):
            return -c * 0.1
        
        c_euler = CSTRSolver.solve_step(
            c=c, c_in=c_in, reaction_func=reactions,
            dt=0.1, dilution_rate=1.0, method='euler'
        )

        c_rk4 = CSTRSolver.solve_step(
            c=c, c_in=c_in, reaction_func=reactions,
            dt=0.1, dilution_rate=1.0, method='rk4'
        )

        assert np.allclose(c_euler, c_rk4, rtol=0.1)

    def test_invalid_method(self):
        """Test : méthode invalide"""
        c = np.ones(5)
        c_in = np.ones(5)

        def reactions(c):
            return np.zeros(5)
        
        with pytest.raises(ValueError):
            CSTRSolver.solve_step(
                c=c, c_in=c_in, reaction_func=reactions,
                dt=0.1, dilution_rate=1.0, method='invalid'
            )