"""
Tests unitaires des processus
"""
from typing import Dict, List
import pytest
import numpy as np

from unittest.mock import Mock, MagicMock, patch, PropertyMock, call
from datetime import datetime

from processes.sludge_process.unified_activated_sludge_process import UnifiedActivatedSludgeProcess
from processes.sludge_process.sludge_metrics import SludgeMetrics
from processes.sludge_process.sludge_model_adapter import SludgeModelAdapter

class TestActivatedSludgeProcess:
    """tests activatedsludgeprocess"""

    @patch('processes.sludge_process.unified_activated_sludge_process.ModelRegistry')
    @patch('processes.sludge_process.unified_activated_sludge_process.SludgeModelAdapter')
    @patch('processes.sludge_process.unified_activated_sludge_process.SludgeMetrics')
    def test_initialization(self, MockMetrics, MockAdapter, MockRegistry):
        """Test : initialisation"""
        mock_registry_instance = MagicMock()
        MockRegistry.get_instance.return_value = mock_registry_instance

        mock_model = MagicMock()
        mock_registry_instance.create_model.return_value = mock_model

        mock_adapter_instance = MagicMock()
        MockAdapter.return_value = mock_adapter_instance
        mock_adapter_instance.size = 13

        config = {
            'model': 'ASM1Model',
            'volume': 5000.0,
            'dissolved_oxygen_setpoint': 2.0
        }

        process = UnifiedActivatedSludgeProcess('test', 'test process', config)

        MockRegistry.get_instance.assert_called_once()
        mock_registry_instance.create_model.assert_called_once_with(
            model_type='ASM1Model',
            params={}
        )
        MockAdapter.assert_called_once()
        assert process.volume == 5000.0

    @patch('processes.sludge_process.unified_activated_sludge_process.CSTRSolver')
    @patch('processes.sludge_process.unified_activated_sludge_process.ModelRegistry')
    def test_process_calls_solver(sef, MockRegistry, MockSolver):
        """Test : process() appelle le solver"""
        mock_registry = MagicMock()
        MockRegistry.get_instance.return_value = mock_registry

        mock_model = MagicMock()
        mock_model.COMPONENT_INDICES = {'so': 7}
        mock_model.dict_to_concentrations.return_value = np.ones(13)*100
        mock_model.concentrations_to_dict.return_value = {}
        mock_registry.create_model.return_value = mock_model

        MockSolver.solve_step.return_value = np.ones(13) * 95

        config = {
            'model': 'ASM1Model',
            'volume': 5000.0,
            'dissolved_oxygen_setpoint': 2.0
        }

        process = UnifiedActivatedSludgeProcess('test', 'test', config)
        process.initialize()

        inputs = {
            'flow': MagicMock(
                flowrate=1000.0,
                temperature=20.0,
                components={'so': 2.0}
            ),
            'flowrate': 1000.0,
            'temperature': 20.0,
            'components': {'so': 2.0}
        }

        with patch.object(process, 'fractionate_input', return_value=inputs):
            process.process(inputs, dt=0.1)

        MockSolver.solve_step.assert_called_once()

    @patch('processes.sludge_process.unified_activated_sludge_process.ModelRegistry')
    def test_fractionate_input_called(self, MockRegistry):
        """Test : fractionate_input est appelé si nécessaire"""
        mock_registry = MagicMock()
        MockRegistry.get_instance.return_value = mock_registry

        mock_model = MagicMock()
        mock_model.COMPONENT_INDICES = {'so': 7}
        mock_model.dict_to_concentrations.return_value = np.ones(13)
        mock_model.concentration_to_dict.return_value = {}
        mock_model.compute_derivatives.return_value = np.zeros(13)
        mock_registry.create_model.return_value = mock_model

        config = {
            'model': 'ASM1Model',
            'volume': 5000.0,
            'dissolved_oxygen_setpoint': 2.0
        }

        process = UnifiedActivatedSludgeProcess('test', 'test', config)
        process.initialize()

        flow_mock = MagicMock()
        flow_mock.flowrate = 1000.0
        flow_mock.temperature = 20.0
        flow_mock.cod = 500.0
        flow_mock.has_model_components.return_value = False

        inputs = {
            'flow': flow_mock,
            'flowrate': 1000.0,
            'temperature': 20.0,
            'components': {}
        }

        with patch.object(process, 'fractionate_input') as mock_fract:
            mock_fract.return_value = inputs
            process.process(inputs, dt=0.1)

            mock_fract.assert_called_once()

    @patch('processes.sludge_process.unified_activated_sludge_process.ModelRegistry')
    def test_initialize_loads_calibration(self, MockRegistry):
        """Test : initialize charge la calibration si disponible"""
        mock_registry = MagicMock()
        MockRegistry.get_instance.return_value = mock_registry

        mock_model = MagicMock()
        mock_model.COMPONENT_INDICES = {'so': 0, 'xbh': 1}

        config = {
            'model': 'ASM1Model',
            'volume': 5000.0,
            'dissolved_oxygen_setpoint': 2.0,
            'use_calibration': True
        }

        process = UnifiedActivatedSludgeProcess('test','test',config)

        with patch.object(process.model_adapter, 'initial_state') as mock_init:
            mock_init.return_value = {'so': 2.0, 'xbh': 2500.0}

            process.initialize()

            mock_init.assert_called_once()
            assert mock_init.call_args[1]['use_calibration'] is True

class TestSludgeMetrics:
    """Tests sludgemetrics"""

    @patch('processes.sludge_process.sludge_metrics.ModelRegistry')
    def test_compute_uses_config(self, MockRegistry):
        """Test : cimpute utilise la configuration du modèle"""

        mock_registry = MagicMock()
        MockRegistry.get_instance.return_value = mock_registry

        mock_def = MagicMock()
        mock_def.get_metrics_dict.return_value = {
            'cod': ['si', 'ss', 'xbh'],
            'tkn': ['snh'],
            'ss': ['xbh'],
            'biomass': ['xbh']
        }
        mock_registry.get_model_definition.return_value = mock_def

        metrics = SludgeMetrics('ASM1Model', mock_registry)

        comp_out = {
            'si': 30.0,
            'ss': 5.0,
            'xbh': 2500.0,
            'snh': 1.5
        }

        c_in = np.zeros(13)

        result = metrics.compute(comp_out, c_in, 1000.0, 0.1, 5000.0, 20.0)

        assert 'cod' in result
        assert 'tkn' in result
        assert 'ss' in result
        assert result['biomass_concentration'] == 2500.0

    @patch('processes.sludge_process.sludge_metrics.ModelRegistry')
    def test_cod_removal_calculation(self, MockRegistry):
        """Test : calcul du taux d'élimination DCO"""
        mock_registry = MagicMock()
        MockRegistry.get_instance.return_value = mock_registry

        mock_def = MagicMock()
        mock_def.get_metrics_dict.return_value = {
            'cod': ['si', 'ss'],
            'soluble_cod': ['ss']
        }
        mock_registry.get_model_definition.return_value = mock_def

        metrics = SludgeMetrics('ASM1Model', mock_registry)

        comp_out = {
            'si': 30.0,
            'ss': 5.0
        }

        c_in_dict = {
            'si': 30.0,
            'ss': 100.0
        }
        c_in = np.array([c_in_dict[k] for k in ['si', 'ss']])

        result = metrics.compute(comp_out, c_in, 1000.0, 0.1, 5000.0, 20.0)

        assert 'cod_removal_rate' in result
        assert result['cod_removal_rate'] >= 0

class TestSludgeModelAdapter:
    """Tests sludgemodeladapter"""

    def test_dict_to_vector_calls_model(self):
        """Test : dict_to_vector appelle la méthode du modèle"""
        mock_model = MagicMock()
        mock_model.dict_to_concentrations.return_value = np.ones(13)
        mock_model.COMPONENT_INDICES = {'so': 0, 'xbh': 1}

        adapter = SludgeModelAdapter(mock_model, 'ASM1')

        test_dict = {'so': 2.0, 'xbh': 2500.0}
        result = adapter.dict_to_vector(test_dict)

        mock_model.dict_to_concentrations.assert_called_once_with(test_dict)
        assert result is not None

    def test_reactions_calls_compute_derivatives(self):
        """Test : reactions appelle compute_derivatives"""
        mock_model = MagicMock()
        mock_model.compute_derivatives.return_value = np.zeros(13)
        mock_model.COMPONENT_INDICES = {}

        adapter = SludgeModelAdapter(mock_model, 'ASM1')

        c = np.ones(13) * 100
        result = adapter.reactions(c)

        mock_model.compute_derivatives.assert_called_once()
        np.testing.assert_array_equal(result, np.zeros(13))

    @patch('processes.sludge_process.sludge_model_adapter.CalibrationCache')
    def test_initial_state_loads_from_cache(self, MockCache):
        """Test : initial_state charge depuis le cache"""
        mock_model = MagicMock()
        mock_model.COMPONENT_INDICES = {'so': 0, 'xbh': 1}

        adapter = SludgeModelAdapter(mock_model, 'ASM1')

        mock_cache_instance = MagicMock()
        MockCache.return_value = mock_cache_instance

        mock_result = MagicMock()
        mock_result.steady_states = {
            'test_process': {'so': 2.0, 'xbh': 2500.0}
        }
        mock_cache_instance.load.return_value = mock_result

        state = adapter.initial_state(
            do_setpoint=2.0,
            process_id='test_process',
            use_calibration=True
        )

        MockCache.assert_called_once()
        assert state is not None
        assert 'so' in state or 'xbh' in state

    def test_initial_state_uses_default(self, asm1_model, asm2d_model, asm3_model):
        """Test : conditions initiales"""
        adapter_asm1 = SludgeModelAdapter(asm1_model, 'ASM1')
        adapter_asm2d = SludgeModelAdapter(asm2d_model, 'ASM2d')
        adapter_asm3 = SludgeModelAdapter(asm3_model, 'ASM3')

        do_setpoint = 2.0

        state_asm1 = adapter_asm1.initial_state(do_setpoint, process_id=None, use_calibration=False)
        state_asm2d = adapter_asm2d.initial_state(do_setpoint, None, False)
        state_asm3 = adapter_asm3.initial_state(do_setpoint, None, False)

        state_list = [state_asm1, state_asm2d, state_asm3]

        for state in state_list:
            assert isinstance(state, dict)
            if 'so' in state:
                assert state['so'] == do_setpoint
            else:
                assert state['so2'] == do_setpoint

            assert state['si'] == 30.0

class TestProcessNode:
    """Tests ProcessNode"""

    def test_fractionate_input_calls_fraction_calss(self):
        """Test : fractionate_input appelle la bonne classe de fraction"""
        from core.process.process_node import ProcessNode

        class TestProcess(ProcessNode):
            def initialize(self) -> None:
                pass

            def process(self, inputs, dt: float):
                return {}
            
            def update_state(self, outputs) -> None:
                pass

            def get_required_inputs(self) -> List[str]:
                return []
            
        process = TestProcess('test', 'test', {})

        mock_flow = MagicMock()
        mock_flow.cod = 500.0
        mock_flow.has_model_components.return_value = False
        mock_flow.extract_measured.return_value = {'cod': 500.0}
        mock_flow.components = {}
        mock_flow.copy.return_value = mock_flow

        inputs = {'flow': mock_flow}

        with patch('importlib.import_module') as mock_import:
            mock_module = MagicMock()
            mock_fraction_class = MagicMock()
            mock_fraction_class.fractionate.return_value = {'si': 25.0, 'ss': 100.0}
            mock_module.ASM1Fraction = mock_fraction_class
            mock_import.return_value = mock_module

            result = process.fractionate_input(inputs, target_model='ASM1')

            mock_fraction_class.fractionate.assert_called_once()