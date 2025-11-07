"""
Tests d'intégration pour les procédés
"""
import pytest
import numpy as np

from datetime import datetime

from core.process.process_factory import ProcessFactory
from core.data.flow_data import FlowData
from processes.sludge_process.activated_sludge_process import ActivatedSludgeProcess


@pytest.fixture
def as_process_asm1(self):
    """Procédé de boues activées avec ASM1"""
    config = {
        'model': 'ASM1Model',
        'volume': 5000.0,
        'dissolved_oxygen_setpoint': 2.0,
        'depth': 4.0,
        'recycle_ratio': 1.0,
        'waste_ratio': 0.01
    }

    process = ActivatedSludgeProcess('test_as', 'Test AS', config)
    process.initialize()
    return process

@pytest.fixture
def as_process_asm2d(self):
    """Procédé de boues activées avec ASM2d"""
    config = {
        'model': 'ASM2dModel',
        'volume': 5000.0,
        'dissolved_oxygen_setpoint': 2.0,
        'depth': 4.0
    }
    process = ActivatedSludgeProcess('test_as2d', 'Test AS2d', config)
    process.initialize()
    return process

@pytest.fixture
def sample_inputs(self, sample_timestamp):
    """Entrées typiques pour le procédé"""
    flow = FlowData(
        timestamp=sample_timestamp,
        flowrate=1000.0,
        temperature=20.0,
        cod=500.0,
        ss=250.0,
        tkn=40.0,
        nh4=28.0,
        no3=0.5,
        po4=8.0
    )

    return {
        'flow': flow,
        'flowrate': 1000.0,
        'temperature': 20.0,
        'components': {}
    }




@pytest.mark.integration
@pytest.mark.processes
class TestActivatedSludgeProcess:
    """Tests d'intégration du précdé de boues activées"""
    
    def test_process_initialization_asm1(self, as_process_asm1):
        """Vérifie l'initialisation correcte du procédé ASM1"""
        assert as_process_asm1.model_type == 'ASM1Model'
        assert as_process_asm1.volume == 5000.0
        assert as_process_asm1.do_setpoint == 2.0
        assert len(as_process_asm1.concentrations) > 0

    def test_process_initialization_asm2d(self, as_process_asm2d):
        """Vérifie l'initialisation correcte du procédé ASM2d"""
        assert as_process_asm2d.model_type == 'ASM2dModel'
        assert as_process_asm2d.volume == 5000.0
        assert as_process_asm2d.do_setpoint == 2.0
        assert len(as_process_asm2d.concentrations) > 0

    def test_process_single_step_asm1(self, as_process_asm1, sample_inputs):
        """Vérifie un pas de traitement ASM1"""
        outputs = as_process_asm1.process(sample_inputs, dt=0.1)

        assert outputs is not None
        assert 'flowrate' in outputs
        assert 'cod' in outputs
        assert 'components' in outputs
        assert outputs['cod'] >= 0

    def test_process_single_step_asm2d(self, as_process_asm2d, sample_inputs):
        """Vérifie un pas de traitement ASM2d"""
        outputs = as_process_asm2d.process(sample_inputs, dt=0.1)

        assert outputs is not None
        assert 'flowrate' in outputs
        assert 'cod' in outputs
        assert 'po4' in outputs

    def test_cod_removal_asm1(self, as_process_asm1, sample_inputs):
        """Vérifie que la DCO diminue"""
        cod_initial = sample_inputs['flow'].cod
        outputs = {}

        for _ in range(10):
            outputs = as_process_asm1.process(sample_inputs, dt=0.1)
            sample_inputs['components'] = outputs['components']

        cod_final = outputs['cod']
        assert cod_final < cod_initial

    def test_metrics_calculation(self, as_process_asm1, sample_inputs):
        """Vérifie que les métriques sont calculées"""
        outputs = as_process_asm1.process(sample_inputs, dt=0.1)

        assert 'hrt_hours' in outputs
        assert 'srt_days' in outputs
        assert 'biomass_concentration' in outputs
        assert 'aeration_energy_kwh' in outputs

    def test_multiple_timesteps_stability(self, as_process_asm1, sample_inputs):
        """Vérifie la stabilité sur plusieurs pas de temps"""
        for i in range(50):
            outputs = as_process_asm1.process(sample_inputs, dt=0.1)

            assert outputs['cod'] >= 0
            assert outputs['ss'] >= 0
            assert np.all(np.isfinite(list(outputs['components'].values())))

            sample_inputs['components'] = outputs['components']

    def test_oxygen_setpoint_maintained(self, as_process_asm1, sample_inputs):
        """Vérifie que la consigne d'oxygène est maintenue"""
        setpoint = 2.0
        outputs = {}

        for _ in range(20):
            outputs = as_process_asm1.process(sample_inputs, dt=0.1)
            sample_inputs['components'] = outputs['components']

        if as_process_asm1.model_type == 'ASM1Model':
            so = outputs['components'].get('so', 0)
        else:
            so = outputs['components'].get('so2', 0)

        assert abs(so - setpoint) < 0.1

    def test_mass_balance_approximation(self, as_process_asm1, sample_inputs):
        """Vérifie approximativement le bilan de masse"""
        cod_in = sample_inputs['flow'].cod

        outputs = as_process_asm1.process(sample_inputs, dt=0.1)
        cod_out = outputs['cod']

        assert cod_out <= cod_in*1.01

    def test_fractionation_automatic(self, as_process_asm1, sample_inputs):
        """Vérifie que le fractionnement automatique fonctionne"""
        assert not sample_inputs['flow'].has_model_components()
        outputs = as_process_asm1.process(sample_inputs, dt=0.1)
        assert len(outputs['components']) > 0

@pytest.mark.integration
class TestProcessFactory:
    """Tests d'intégration de ProcessFactory"""

    def test_create_single_process(self):
        """Vérifie la création d'un procédé unique"""
        config = {
            'node_id': 'test_as',
            'type': 'ActivatedSludgeProcess',
            'name': 'Test AS',
            'config': {
                'model': 'ASM1Model',
                'volume': 5000.0,
                'dissolved_oxygen_setpoint': 2.0
            }
        }

        process = ProcessFactory.create_process(config)

        assert process is not None
        assert process.node_id == 'test_as'
        assert isinstance(process, ActivatedSludgeProcess)

    def test_create_from_config(self, minimal_config):
        """Vérifie la création depuis une configuration complète"""
        processes = ProcessFactory.create_from_config(minimal_config)

        assert len(processes) == 1
        assert processes[0].node_id == 'test_as1'

    def test_create_multiple_processes(self, multi_process_config):
        """Vérifie la création de plusieurs procédés"""
        processes = ProcessFactory.create_from_config(multi_process_config)

        assert len(processes) == 2
        assert processes[0].node_id == 'as1'
        assert processes[1].node_id == 'as2'

    def test_connections_setup(self, multi_process_config):
        """Vérifie la configuration des connexions"""
        processes = ProcessFactory.create_from_config(multi_process_config)

        assert 'influent' in processes[0].upstream_nodes
        assert 'as2' in processes[0].downstream_nodes
        assert 'as1' in processes[1].upstream_nodes

    def test_invalid_process_type(self):
        """Vérifie la gestion d'un type de procédé invalide"""
        config = {
            'node_id': 'test',
            'type': 'InvalidProcess',
            'name': 'Test',
            'config': {}
        }
        with pytest.raises(ValueError):
            ProcessFactory.create_process(config)

@pytest.mark.integration
class TestProcessChain:
    """Tests d'intégration d'une chaîne de procédés"""

    def test_two_process_chain(self, multi_process_config, sample_timestamp):
        """Vérifie le traitement à travers deux procédés"""
        processes = ProcessFactory.create_from_config(multi_process_config)

        for p in processes:
            p.initialize()

        flow_in = FlowData(
            timestamp=sample_timestamp,
            flowrate=1000.0,
            temperature=20.0,
            cod=500.0,
            ss=250.0,
            tkn=40.0,
            nh4=28.0
        )

        inputs1 = {
            'flow': flow_in,
            'flowrate': 1000.0,
            'temperature': 20.0,
            'components': {}
        }
        outputs1 = processes[0].process(inputs1, dt=0.1)

        inputs2 = {
            'flow': flow_in,
            'flowrate': outputs1['flowrate'],
            'temperature': outputs1['temperature'],
            'components': outputs1['components']
        }
        outputs2 = processes[1].process(inputs2, dt=0.1)

        assert outputs2['cod'] >= 0
        assert outputs2['cod'] <= outputs1['cod']

    def test_process_state_persistence(self, as_process_asm1, sample_inputs):
        """Vérifie que l'état du procédé persiste entre les appels"""
        outputs1 = as_process_asm1.process(sample_inputs, dt=0.1)
        state1 = as_process_asm1.get_state()

        sample_inputs['components'] = outputs1['components']
        outputs2 = as_process_asm1.process(sample_inputs, dt=0.1)
        state2 = as_process_asm1.get_state()

        assert state1 != state2