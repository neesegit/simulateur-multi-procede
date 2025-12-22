"""
Tests unitaires pour la configuration et validation
"""
import pytest
import json

from pathlib import Path
from unittest.mock import Mock, patch, mock_open

from interfaces.config.loader import ConfigLoader
from interfaces.config.validator import ConfigValidator
from interfaces.config.defaults import ConfigDefaults
from interfaces.config.schema.config_schema import ConfigSchema

class TestConfigValidator:
    """Tests pour ConfigValidator"""

    def test_validate_minimal_valid_config(self, minimal_config):
        """Test : config minimale valide"""
        ConfigValidator.validate(minimal_config)

    def test_missing_simulation_section(self):
        """Test : section simulation manquante"""
        config = {
            'name': 'test',
            'simulation': {},
            'processes': []
        }

        with pytest.raises(ValueError):
            ConfigValidator.validate(config)

    def test_end_before_start_time(self):
        """Test : end_time avant start_time"""
        config = {
            'name': 'test',
            'simulation': {
                'start_time': '2025-12-11T12:00:00',
                'end_time': '2025-12-11T06:00:00',
                'timestep_hours': 0.1
            },
            'influent': {'flowrate': 1000, 'temperature': 20},
            'processes': []
        }

        with pytest.raises(ValueError) as exc_info:
            ConfigValidator.validate(config)

        assert "end_time" in str(exc_info.value).lower() or "après" in str(exc_info.value).lower()

    def test_invalid_timestep(self):
        """Test : timestep invalide"""
        config = {
            'name': 'test',
            'simulation': {
                'start_time': '2025-12-11T00:00:00',
                'end_time': '2025-12-11T12:00:00',
                'timestep_hours': -0.1
            },
            'influent': {'flowrate': 1000.0, 'temperature': 20.0},
            'processes': []
        }

        with pytest.raises(ValueError):
            ConfigValidator.validate(config)

    def test_negative_flowrate(self):
        """Test : flowrate négatif"""
        config = {
            'name': 'test',
            'simulation': {
                'start_time': '2025-12-11T00:00:00',
                'end_time': '2025-12-11T12:00:00',
                'timestep_hours': 0.1
            },
            'influent': {
                'flowrate': -1000.0,
                'temperature': 20.0
            },
            'processes': []
        }

        with pytest.raises(ValueError):
            ConfigValidator.validate(config)

    def test_invalid_connection_source(self):
        """Test : source de connexion invalide"""
        config = {
            'name': 'test',
            'simulation': {
                'start_time': '2025-12-11T00:00:00',
                'end_time': '2025-12-11T12:00:00',
                'timestep_hours': 0.1
            },
            'influent': {'flowrate': 1000, 'temperature': 20},
            'processes': [
                {
                    'node_id': 'proc1',
                    'type': 'ActivatedSludgeProcess',
                    'name': 'Proc 1'
                }
            ],
            'connections': [
                {
                    'source': 'nonexistent',
                    'target': 'proc1',
                    'fraction': 1.0,
                    'is_recycle': False
                }
            ]
        }

        with pytest.raises(ValueError, match="source inconnue"):
            ConfigValidator.validate(config)

    def test_duplicate_node_id(self):
        """Test : node_id dupliqué"""
        config = {
            'name': 'test',
            'simulation': {
                'start_time': '2025-12-11T00:00:00',
                'end_time': '2025-12-11T12:00:00',
                'timestep_hours': 0.1
            },
            'influent': {'flowrate': 1000, 'temperature': 20},
            'processes': [
                {
                    'node_id': 'proc1',
                    'type': 'ActivatedSludgeProcess',
                    'name': 'Proc 1'
                },
                {
                    'node_id': 'proc1',
                    'type': 'ActivatedSludgeProcess',
                    'name': 'Proc 2'
                }
            ]
        }

        with pytest.raises(ValueError, match="dupliqué"):
            ConfigValidator.validate(config)

class TestConfigLoader:
    """Tests pour ConfigLoader"""

    def test_load_json_file(self, minimal_config, tmp_path):
        """Test : chargement fichier JSON"""
        config_path = tmp_path / "test_config.json"
        with open(config_path, 'w') as f:
            json.dump(minimal_config, f)

        loaded = ConfigLoader.load(config_path)

        assert loaded['name'] == minimal_config['name']
        assert loaded['simulation']['timestep_hours'] == minimal_config['simulation']['timestep_hours']

    def test_load_nonexistent_file(self):
        """Test : fichier inexistant"""
        with pytest.raises(FileNotFoundError):
            ConfigLoader.load(Path('nonexistent.json'))

    def test_save_json(self, minimal_config, tmp_path):
        """Test : sauvegarde JSON"""
        output_path = tmp_path / "saved_config.json"

        ConfigLoader.save(minimal_config, output_path)

        assert output_path.exists()

        with open(output_path) as f:
            loaded = json.load(f)

        assert loaded['name'] == minimal_config['name']

    def test_unsupported_format(self, tmp_path):
        """Test : format non supporté"""
        config_path = tmp_path / "config.txt"
        config_path.write_text("some config")

        with pytest.raises(ValueError, match="Format de fichier non supporté"):
            ConfigLoader.load(config_path)

    def test_applies_defaults(self, tmp_path):
        """Test : applique les valeurs par défaut"""
        config = {
            'simulation': {
                'start_time': '2025-12-11T00:00:00',
                'end_time': '2025-12-11T12:00:00',
                'timestep_hours': 0.1
            },
            'influent': {'flowrate': 1000, 'temperature': 20},
            'processes': [
                {
                    'node_id': 'p1',
                    'type': 'ActivatedSludgeProcess',
                    'name': 'p1'
                }
            ]
        }

        config_path = tmp_path / "config.json"
        with open(config_path, 'w') as f:
            json.dump(config, f)

        loaded = ConfigLoader.load(config_path)

        assert 'name' in loaded

    @patch('builtins.open', new_callable=mock_open, read_data='invalid json{')
    def test_invalid_json(self, mock_file):
        """Test : JSON invalide"""
        with patch('pathlib.Path.exists', return_value=True):
            with pytest.raises(json.JSONDecodeError):
                ConfigLoader.load(Path('test.json'))

class TestConfigDefaults:
    """Tests pour ConfigDefaults"""
    
    def test_apply_defaults_adds_name(self):
        """Test : ajoute un nom si manquant"""
        config = {
            'simulation': {},
            'influent': {},
            'processes': []
        }

        result = ConfigDefaults.apply_defaults(config)

        assert 'name' in result
        assert 'simulation_' in result['name']

    def test_apply_defaults_preserves_existing(self):
        """Test : préserve les valeurs existantes"""
        config = {
            'name': 'my_sim',
            'description': 'my description',
            'simulation': {},
            'influent': {},
            'processes': []
        }

        result = ConfigDefaults.apply_defaults(config)

        assert result['name'] == 'my_sim'
        assert result['description'] == 'my description'

    def test_apply_influent_defaults(self):
        """Test : défauts pour influent"""
        config = {
            'name': 'test',
            'simulation': {},
            'influent': {
                'flowrate': 1000,
                'temperature': 20
            },
            'processes': []
        }

        result = ConfigDefaults.apply_defaults(config)

        assert 'auto_fractionate' in result['influent']

    def test_apply_process_defaults(self):
        """Test : défauts pour procédés"""
        config = {
            'name': 'test',
            'simulation': {},
            'influent': {},
            'processes': [
                {
                    'node_id': 'proc1',
                    'type': 'ActivatedSludgeProcess',
                    'name': 'Process 1',
                    'config': {
                        'model': 'ASM1Model',
                        'volume': 5000.0
                    }
                }
            ]
        }

        result = ConfigDefaults.apply_defaults(config)

        proc_config = result['processes'][0]['config']

        assert 'dissolved_oxygen_setpoint' in proc_config
        assert 'depth' in proc_config

class TestConfigSchema:
    """Tests pour configschema"""

    def test_get_required_fiedls(self):
        """Test : champs requis"""
        required = ConfigSchema.get_required_fields_for_section('simulation')

        assert 'start_time' in required
        assert 'end_time' in required
        assert 'timestep_hours' in required

    def test_get_value_range(self):
        """Test : plage de valeurs"""
        min_val, max_val = ConfigSchema.get_value_range('flowrate')

        assert min_val is not None
        assert max_val is not None
        assert min_val < max_val

    def test_is_valid_process_type(self):
        """Test : validation type de procédé"""
        assert ConfigSchema.is_valid_process_type('ActivatedSludgeProcess')
        assert not ConfigSchema.is_valid_process_type('InvalidProcess')

    def test_get_supported_process_types(self):
        """Test : liste des types supportés"""
        types = ConfigSchema.get_supported_process_types()

        assert isinstance(types, list)
        assert len(types) > 0
        assert 'ActivatedSludgeProcess' in types

class TestConfigEdgeCases:
    """tests de cas limites"""

    def test_empty_processes_list(self):
        """test : liste de procédés vide"""
        config = {
            'name': 'test',
            'simulation': {
                'start_time': '2025-12-11T00:00:00',
                'end_time': '2025-12-11T12:00:00',
                'timestep_hours': 0.1
            },
            'influent': {'flowrate': 1000, 'temperature': 20},
            'processes': []
        }

        with pytest.raises(ValueError, match="Au moins un procédé"):
            ConfigValidator.validate(config)

    def test_very_small_timestep(self):
        """Test : timestep très petit"""

        config = {
            'name': 'test',
            'simulation': {
                'start_time': '2025-12-11T00:00:00',
                'end_time': '2025-12-11T12:00:00',
                'timestep_hours': 0.0001
            },
            'influent': {'flowrate': 1000, 'temperature': 20},
            'processes': [{'node_id': 'p1', 'type': 'ActivatedSludgeProcess', 'name': 'P1'}]
        }

        with pytest.raises(ValueError):
            ConfigValidator.validate(config)

    def test_very_large_volume(self):
        """Test : volume très grand"""
        config = {
            'name': 'test',
            'simulation': {
                'start_time': '2025-12-11T00:00:00',
                'end_time': '2025-12-11T12:00:00',
                'timestep_hours': 0.1
            },
            'influent': {'flowrate': 1000, 'temperature': 20},
            'processes': [
                {
                    'node_id': 'p1',
                    'type': 'ActivatedSludgeProcess',
                    'name': 'p1',
                    'config': {
                        'volume': 1000000.0
                    }
                }
            ]
        }

        ConfigValidator.validate(config)