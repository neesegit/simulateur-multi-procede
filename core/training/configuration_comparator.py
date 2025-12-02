import hashlib
import json

from typing import Dict, Any

class MLConfigurationComparator:
    """Compare les configurations ML pour déterminer si ré-entraînement nécessaire"""

    @staticmethod
    def normalize_ml_config(config: Dict[str, Any]) -> Dict[str, Any]:
        """Normalise une configuration ML pour le hashing"""
        relevant_keys = [
            'model',
            'volume',
            'model_parameters',
            'training_data_path',
            'training_params'
        ]

        if 'config' in config and isinstance(config['config'], dict):
            base_config = config['config']
        else:
            base_config = config

        normalized = {}

        for key in relevant_keys:
            if key in base_config:
                value = base_config[key]
                if isinstance(value, float):
                    normalized[key] = round(value, 6)
                else:
                    normalized[key] = value
        
        return normalized
    
    @staticmethod
    def compute_hash(config: Dict[str, Any]) -> str:
        """Calcule un hash de la configuration"""
        normalized = MLConfigurationComparator.normalize_ml_config(config)
        config_json = json.dumps(normalized, sort_keys=True, default=str).encode('utf-8')
        return hashlib.sha256(config_json).hexdigest()
    
    @staticmethod
    def compare_configs(config1: Dict[str, Any], config2: Dict[str, Any]) -> Dict[str, Any]:
        """Compare deux configurations en détail"""
        norm1 = MLConfigurationComparator.normalize_ml_config(config1)
        norm2 = MLConfigurationComparator.normalize_ml_config(config2)

        differences = {
            'added': {},
            'removed': {},
            'modified': {}
        }

        all_keys = set(norm1.keys()) | set(norm2.keys())

        for key in all_keys:
            if key not in norm1:
                differences['removed'][key] = norm2[key]
            elif key not in norm2:
                differences['added'][key] = norm1[key]
            elif norm1[key] != norm2[key]:
                differences['modified'][key] = {
                    'old': norm2[key],
                    'new': norm1[key]
                }
        
        return differences