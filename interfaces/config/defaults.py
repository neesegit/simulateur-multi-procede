"""
Valeurs par défaut et templates de configuration
"""
from typing import Dict, Any
from datetime import datetime

class ConfigDefaults:
    """
    Valeurs par défaut pour les configurations
    """

    INFLUENT_DEFAULTS = {
        'auto_fractionate': True,
        'composition': {}
    }

    TYPICAL_URBAN_WASTEWATER = {
        'cod': 500.0,
        'ss': 250.0,
        'tkn': 40.0,
        'nh4': 28.0,
        'no3': 0.5,
        'po4': 8.0,
        'alkalinity': 6.0
    }

    PROCESS_DEFAULTS = {
        'ActivatedSludgeProcess': {
            'volume': 5000.0,
            'depth': 4.0,
            'dissolved_oxygen_setpoint': 2.0,
            'recycle_ratio': 1.0,
            'waste_ratio': 0.01
        },
    }

    @staticmethod
    def apply_defaults(config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Applique les valeurs par défaut pour les champs optionnels

        Args:
            config (Dict[str, Any]): Configuration

        Returns:
            Dict[str, Any]: Configuration avec valeurs par défaut appliquées
        """
        if 'name' not in config:
            config['name'] = f"simulation_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        if 'description' not in config:
            config['description'] = "Simulation générée automatiquement"

        ConfigDefaults._apply_influent_defaults(config['influent'])

        for proc in config.get('processes', []):
            ConfigDefaults._apply_process_defaults(proc)

        return config


    @staticmethod
    def _apply_influent_defaults(influent: Dict[str, Any]) -> None:
        """Applique les valeurs par défaut pour l'influent"""
        for key, value in ConfigDefaults.INFLUENT_DEFAULTS.items():
            influent.setdefault(key, value)

    @staticmethod
    def _apply_process_defaults(proc: Dict[str, Any]) -> None:
        """Applique les valeurs par défaut pour un procédé"""
        proc.setdefault('config', {})

        proc_type = proc.get('type')
        if proc_type in ConfigDefaults.PROCESS_DEFAULTS:
            default = ConfigDefaults.PROCESS_DEFAULTS[proc_type]
            for key, value in default.items():
                proc['config'].setdefault(key, value)

    