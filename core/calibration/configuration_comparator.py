import json
import hashlib

from typing import Dict, Any

from .dataclass.calibration_metadata import CalibrationMetadata

class ConfigurationComparator:
    """Compare une configuration avec une calibration sauvegardée"""

    @staticmethod
    def compute_hash(config: Dict[str, Any]) -> str:
        """Calcule un hash SHA256 de la configuration"""
        config_json = json.dumps(
            config,
            sort_keys=True,
            default=str
        ).encode('utf-8')
        return hashlib.sha256(config_json).hexdigest()
    
    @staticmethod
    def is_config_changed(
        current_config: Dict[str, Any],
        cached_metadata: CalibrationMetadata
    ) -> bool:
        """Vérifie si la configuration a changé depuis la calibration"""
        current_hash = ConfigurationComparator.compute_hash(current_config)
        return current_hash != cached_metadata.config_hash
    
    @staticmethod
    def compare_configs(
        config1: Dict[str, Any],
        config2: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Compare deux configurations en détail"""
        differences = {
            'added': {},
            'removed': {},
            'modified': {}
        }

        all_keys = set(config1.keys()) | set(config2.keys())

        for key in all_keys:
            if key not in config1:
                differences['removed'][key] = config2[key]
            elif key not in config2:
                differences['added'][key] = config1[key]
            elif config1[key] != config2[key]:
                differences['modified'][key] = {
                    'old': config2[key],
                    'new': config1[key]
                }
        return differences