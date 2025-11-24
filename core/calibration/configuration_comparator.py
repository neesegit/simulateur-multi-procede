import json
import hashlib

from typing import Dict, Any

from .dataclass.calibration_metadata import CalibrationMetadata

class ConfigurationComparator:
    """Compare une configuration avec une calibration sauvegardée"""

    @staticmethod
    def normalize_process_config(config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Normalise une configuration de procédé pour le hashing
        Garde uniquement les champs pertinents qui impactent la calibration

        Args:
            config (Dict[str, Any]): Configuration brute

        Returns:
            Dict[str, Any]: Configuration normalisée
        """
        relevant_keys = [
            'volume',
            'dissolved_oxygen_setpoint',
            'depth',
            'recycle_ratio',
            'waste_ratio',
            'model',
            'model_parameters'
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
        """Calcule un hash SHA256 de la configuration"""
        normalized = ConfigurationComparator.normalize_process_config(config)
        config_json = json.dumps(
            normalized,
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
        norm1 = ConfigurationComparator.normalize_process_config(config1)
        norm2 = ConfigurationComparator.normalize_process_config(config2)

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