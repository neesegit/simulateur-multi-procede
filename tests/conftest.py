"""
Fixtures pytest partagées entre tous les tests
"""
import pytest
import numpy as np

from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any

from core.data.flow_data import FlowData
from core.data.databuses import DataBus
from core.data.simulation_flow import SimulationFlow

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

# ===================================
# Fixtures de données
# ===================================

@pytest.fixture
def sample_flow_data(sample_timestamp):
    """Flowdata simple pour les tests"""
    return FlowData(
        timestamp=sample_timestamp,
        flowrate=1000.0,
        temperature=20.0,
        cod=500.0,
        ss=250.0,
        tkn=40.0,
        nh4=28.0,
        no3=0.5,
        po4=8.0,
        source_node="test_node"
    )

@pytest.fixture
def sample_asm1_components():
    """Composants ASM1 typiques"""
    return {
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

@pytest.fixture
def sample_asm2d_components():
    """Composants ASM2d typiques"""
    return {
        'so2': 2.0,
        'sf': 10.0,
        'sa': 5.0,
        'snh4': 2.0,
        'sno3': 5.0,
        'spo4': 1.0,
        'si': 30.0,
        'salk': 5.0,
        'sn2': 0.0,
        'xi': 25.0,
        'xs': 100.0,
        'xh': 1500.0,
        'xpao': 200.0,
        'xpp': 50.0,
        'xpha': 10.0,
        'xaut': 80.0,
        'xtss': 2000.0,
        'xmeoh': 50.0,
        'xmep': 0.0
    }

# =====================================
# Fixtures de configuration
# =====================================

@pytest.fixture
def minimal_config():
    """Configuration minimale valide"""
    return {
        'name': 'test_simulation',
        'description': 'Test simulation',
        'simulation': {
            'start_time': '2025-01-01T00:00:00',
            'end_time': '2025-01-01T01:00:00',
            'timestep_hours': 0.1
        },
        'influent': {
            'flowrate': 1000.0,
            'temperature': 20.0,
            'auto_fractionate': True,
            'composition': {
                'cod': 500.0,
                'ss': 250.0,
                'tkn': 40.0,
                'nh4': 28.0,
                'no3': 0.5,
                'po4': 8.0,
                'alkalinity': 6.0
            }
        },
        'processes': [
            {
                'node_id': 'test_as1',
                'type': 'ActivatedSludgeProcess',
                'name': 'Test AS',
                'config': {
                    'model': 'ASM1Model',
                    'volume': 5000.0,
                    'dissolved_oxygen_setpoint': 2.0,
                    'depth': 4.0,
                    'recycle_ratio': 1.0,
                    'waste_raito': 0.01
                }
            }
        ],
        'connections': [
            {
                'source': 'influent',
                'target': 'test_as1',
                'fraction': 1.0,
                'is_recycle': False
            }
        ]
    }

@pytest.fixture
def multi_process_config(minimal_config):
    """Configuration avec plusieus procédés"""
    config = minimal_config.copy()
    config['processes'] = [
        {
            'node_id': 'as1',
            'type': 'ActivatedSludgeProcess',
            'name': 'AS 1',
            'config': {
                'model': 'ASM1Model',
                'volume': 3000.0,
                'dissolved_oxygen_setpoint': 2.0,
                'depth': 4.0
            }
        },
        {
            'node_id': 'as2',
            'type': 'ActivatedSludgeProcess',
            'name': 'AS 2',
            'config': {
                'model': 'ASM1Model',
                'volume': 2000.0,
                'dissolved_oxygen_setpoint': 1.5,
                'depth': 3.5
            }
        }
    ]
    config['connections'] = [
        {'source': 'influent', 'target': 'as1', 'fraction': 1.0, 'is_recycle': False},
        {'dource': 'as1', 'target': 'as2', 'fraction': 1.0, 'is_recycle': False}
    ]
    return config

# =====================================
# Fixtures de composants core
# =====================================

@pytest.fixture
def databus():
    """DataBus vide"""
    return DataBus()

@pytest.fixture
def simulation_flow():
    """SimulationFlow vide"""
    return SimulationFlow()

@pytest.fixture
def databus_with_data(databus, sample_flow_data):
    """DataBus avec des données de test"""
    databus.write_flow('influent', sample_flow_data)
    return databus

# =====================================
# Fixtures de modèles
# =====================================

@pytest.fixture
def asm1_model():
    """Instance du modèle ASM1"""
    from models.asm1.model import ASM1Model
    return ASM1Model()

@pytest.fixture
def asm2d_model():
    """Instance du modèle ASM2d"""
    from models.asm2d.model import ASM2dModel
    return ASM2dModel()

# =====================================
# Utilitaires
# =====================================

@pytest.fixture
def assert_concentrations_valid():
    """Helper pour vérifier la validité des concentrations"""
    def _check(concentrations: np.ndarray):
        assert np.all(concentrations >= 0), 'Concentrations négatives détectées'
        assert np.all(np.isfinite(concentrations)), 'Valeurs infinies/NaN détectées'
        assert not np.any(np.isnan(concentrations)), 'NaN détectés'
    return _check

@pytest.fixture
def assert_mass_balance():
    """Helper pour vérifier le bilan de masse"""
    def _check(c_in: np.ndarray, c_out: np.ndarray, tolerance: float=0.1):
        """Vérifie que la masse totale est conservée (à tolérance près)"""
        mass_in = np.sum(c_in)
        mass_out = np.sum(c_out)
        relative_error = abs(mass_in - mass_out) / mass_in if mass_in > 0 else 0
        assert relative_error < tolerance, f"Bilan de masse non respecté : {relative_error*100:.2f}% d'écart"
    return _check

# =====================================
# Hooks pytest
# =====================================

def pytest_configure(config):
    """Configuration globale de pytest"""
    config.addinivalue_line("markers", "unit: Tests unitaires rapides")
    config.addinivalue_line("markers", "intergration: Tests d'intégration")
    config.addinivalue_line("markers", "e2e: Tests end-to-end complets")

def pytest_collection_modifyitems(config, items):
    """Ajoute automatiquement des markers selon le chemin du test"""
    for item in items:
        # Ajoute marker selon le dossier
        if "unit" in str(item.fspath):
            item.add_marker(pytest.mark.unit)
        elif "integration" in str(item.fspath):
            item.add_marker(pytest.mark.integration)
        elif "e2e" in str(item.fspath):
            item.add_marker(pytest.mark.e2e)
            item.add_marker(pytest.mark.slow)