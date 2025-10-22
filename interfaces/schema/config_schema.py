"""
Schémas de validation pour les configurations

Ce module définit les structures attendues pour les fichiers de configuration
"""
from typing import Dict, List, Any

class ConfigSchema:
    """
    Définit les schémas de validation pour les configurations
    """

    REQUIRED_FIELDS: Dict[str, List[str]] = {
        'simulation': ['start_time', 'end_time', 'timestep_hours'],
        'influent': ['flowrate', 'temperature', 'model_type'],
        'processes': []
    }

    OPTIONAL_FIELDS: Dict[str, List[str]] = {
        'simulation': [],
        'influent': ['auto_fractionate', 'composition'],
        'processes': ['config', 'connections']
    }

    PROCESS_REQUIRED_FIELDS: List[str] = ['node_id', 'type', 'name']

    VALUE_RANGES: Dict[str, tuple] = {
        'timestep_hours': (0.001, 24.0),
        'flowrate': (0.1, 1e6),
        'temperature': (0.0, 50.0),
        'volume': (1.0, 1e6),
        'depth': (0.1, 20.0),
        'area': (1.0, 1e6)
    }

    SUPPORTED_MODEL_TYPES: List[str] = [
        'ASM1',
        'ASM2d',
        'ASM3',
        'ML'
    ]

    SUPPORTED_PROCESS_TYPES: List[str] = [
        'ActivatedSludgeProcess',
        'ASM1Process' # Redirige vers ActivatedSludgeProcess
    ]

    @staticmethod
    def get_required_fields_for_section(section: str) -> List[str]:
        """
        Retourne les champs requis pour une section

        Args:
            section (str): Nom de la section ('simulation', 'influent', etc)

        Returns:
            List[str]: Liste des champs requis
        """
        return ConfigSchema.REQUIRED_FIELDS.get(section, [])
    
    @staticmethod
    def get_value_range(field: str) -> tuple:
        """
        Retourne la plage de valeurs acceptables pour un champ

        Args:
            field (str): Nom du champ

        Returns:
            tuple: Tuple(min, max) ou None si pas de contrainte
        """
        return ConfigSchema.VALUE_RANGES.get(field, (None, None))
    
    @staticmethod
    def is_valid_model_type(model_type: str) -> bool:
        """
        Vérifie si le type de modèle est supporté
        """
        return model_type.upper() in [m.upper() for m in ConfigSchema.SUPPORTED_MODEL_TYPES]
    
    @staticmethod
    def is_valid_process_type(process_type: str) -> bool:
        """
        Vérifie si le type de procédé est supporté
        """
        return process_type in ConfigSchema.SUPPORTED_PROCESS_TYPES