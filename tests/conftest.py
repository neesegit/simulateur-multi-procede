"""
Fixtures pytest partagées entre tous les tests
"""
import pytest
import numpy as np

from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any

from unittest.mock import Mock, MagicMock

from core.data.flow_data import FlowData
from core.data.databuses import DataBus
from core.data.simulation_flow import SimulationFlow
from core.model.model_registry import ModelRegistry

from models.empyrical.asm1.model import ASM1Model
from models.empyrical.asm2d.model import ASM2dModel
from models.empyrical.asm3.model import ASM3Model

# ====================================
# Fixtures de base
# ====================================

@pytest.fixture
def temp_dir(tmp_path):
    """Crée un répertoire temporaire pour les tests"""
    test_dir = tmp_path / "test_output"
    test_dir.mkdir()
    return test_dir

@pytest.fixture
def sample_timestamp():
    """Timestamp de référence pour les tests"""
    return datetime(2025, 1, 1, 0, 0, 0)

# ====================================
# Fixtures flow data
# ====================================

@pytest.fixture
def basic_flow_data(sample_timestamp):
    """FlowData basique pour tests"""
    return FlowData(
        timestamp=sample_timestamp,
        flowrate=1000.0,
        temperature=20.0,
        cod=500.0,
        tss=250.0,
        tkn=40.0,
        nh4=28.0,
        no3=0.5,
        po4=8.0,
        source_node='influent'
    )

@pytest.fixture
def asm1_flow_data(sample_timestamp):
    """FlowData avec composants ASM1"""
    flow = FlowData(
        timestamp=sample_timestamp,
        flowrate=1000.0,
        temperature=20.0,
        source_node='test_process',
        
    )
    flow.components = {
        'si': 30.0,
        'ss': 5.0,
        'xi': 25.0,
        'xs': 100.0,
        'xbh': 2500.0,
        'xba': 150.0,
        'xp': 450.0,
        'so': 2.0,
        'sno': 5.0,
        'snh': 2.0,
        'snd': 1.0,
        'xnd': 5.0,
        'salk': 7.0
    }
    return flow

# ====================================
# Fixtures Modèles
# ====================================

@pytest.fixture
def asm1_model():
    """Instance du modèle ASM1"""
    return ASM1Model()

@pytest.fixture
def asm2_model():
    """Instance du modèle ASM2d"""
    return ASM2dModel()

@pytest.fixture
def asm3_model():
    """Instance du modèle ASM3"""
    return ASM3Model()

@pytest.fixture
def mock_model():
    """Mock d'un modèle pour tests isolés"""
    mock = MagicMock()
    mock.compute_derivatives.return_value = np.zeros(13)
    mock.COMPONENT_INDICES = {
        'si': 0, 'ss': 1, 'xi': 2, 'xs': 3,
        'xbh': 4, 'xba': 5, 'xp': 6, 'so': 7,
        'sno': 8, 'snh': 9, 'snd': 10, 'xnd': 11,
        'salk': 12
    }
    mock.get_component_names.return_value = list(mock.COMPONENT_INDICES.keys())
    return mock

@pytest.fixture
def model_registry():
    """Registry des modèles"""
    return ModelRegistry.get_instance()

# ====================================
# Fixtures configuration
# ====================================

@pytest.fixture
def minimal_config():
    """Configuration minimale valide"""
    return {
        'name': 'test_simulation',
        'description': 'Test',
        'simulation': {
            'start_time': '2025-12-11T00:00:00',
            'end_time': '2025-12-11T01:00:00',
            'timestep_hours': 0.1
        },
        'influent': {
            'flowrate': 1000.0,
            'temperature': 20.0,
            'composition': {
                'cod': 500.0,
                'tss': 250.0,
                'tkn': 40.0,
                'nh4': 28.0,
                'no3': 0.5,
                'po4': 8.0,
                'alkalinity': 6.0
            }
        },
        'processes': [
            {
                'node_id': 'test_process',
                'type': 'ActivatedSludgeProcess',
                'name': 'Test Process',
                'config': {
                    'model': 'ASM1Model',
                    'volume': 5000.0,
                    'dissolved_oxygen_setpoint': 2.0,
                    'depth': 4.0,
                    'recycle_ratio': 1.0,
                    'waste_ratio': 0.01
                }
            }
        ],
        'connections': [
            {
                'source': 'influent',
                'target': 'test_process',
                'fraction': 1.0,
                'is_recycle': False
            }
        ]
    }

@pytest.fixture
def invalid_config():
    """Configuration invalide pour tester la validation"""
    return {
        'name': 'invalid',
        'simulation': {
            'start_time': '2025-12-11T00:00:00',
            'end_time': '2025-12-10T00:00:00',
            'timestep_hours': -1
        }
    }

# ====================================
# Fixtures mock pour tests isolés
# ====================================

@pytest.fixture
def mock_databus():
    """Mock du DataBus"""
    mock = MagicMock()
    mock.read_flow.return_value = None
    mock.write_flow.return_value = None
    return mock

@pytest.fixture
def mock_calibration_cache():
    """Mock du cache de calibration"""
    mock = MagicMock()
    mock.exists.return_value = False
    mock.load.return_value = None
    mock.save.return_value = Path('mock_cache.json')
    return mock

@pytest.fixture
def mock_process_node():
    """Mock d'un ProcessNode"""
    mock = MagicMock()
    mock.node_id = 'mock_process'
    mock.name = 'Mock Process'
    mock.upstream_nodes = []
    mock.downstream_nodes = []
    mock.process.return_value = {
        'flowrate': 1000.0,
        'temperature': 20.0,
        'cod': 50.0,
        'tss': 2000.0
    }
    return mock

# ====================================
# Fixtures pour tests ml
# ====================================

@pytest.fixture
def sample_training_data():
    """Données d'entraînement pour modèles ML"""
    np.random.seed(42)
    n_samples = 100
    X = np.random.randn(n_samples, 10)
    y = np.random.randn(n_samples, 7)
    return X, y

# ====================================
# Fixtures pour tests de résultats
# ====================================

@pytest.fixture
def sample_simulation_results():
    """Résultats de simulation pour tests"""
    return {
        'metadata': {
            'sim_name': 'test_sim',
            'start_time': '2025-12-11T00:00:00',
            'end_time': '2025-12-11T01:00:00',
            'timestep': 0.1,
            'steps_completed': 10
        },
        'history': {
            'test_process': [
                {
                    'timestamp': '2025-12-11T00:00:00',
                    'flowrate': 1000.0,
                    'cod': 50.0,
                    'tss': 2000.0
                }
            ] * 10
        },
        'statistics': {
            'test_process': {
                'avg_cod': 50.0,
                'avg_flowrate': 1000.0
            }
        }
    }

# ====================================
# Helpers pour assertions
# ====================================

@pytest.fixture
def assert_flow_valid():
    """Helper pour valider un FlowData"""
    def _assert(flow: FlowData):
        assert flow.flowrate > 0, "Flowrate doit être positif"
        assert 0 <= flow.temperature <= 50, "Température hors limites"
        assert flow.timestamp is not None, "Timestamp manquant"
        assert isinstance(flow.components, dict), "Components doit être un dict"
    return _assert

@pytest.fixture
def assert_concentrations_positive():
    """Helper pour vérifier que les concentrations sont positives"""
    def _assert(concentrations: np.ndarray):
        assert np.all(concentrations >= 0), "Concentrations négatives détectées"
    return _assert