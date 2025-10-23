"""
Schémas de validation pour les configurations

Ce module définit les structures attendues pour les fichiers de configuration
"""
from typing import Dict, List, Any
from core.process.process_registry import ProcessRegistry

class ConfigSchema:
    """
    Définit les schémas de validation pour les configurations
    """

    REQUIRED_FIELDS: Dict[str, List[str]] = {
        'simulation': ['start_time', 'end_time', 'timestep_hours'],
        'influent': ['flowrate', 'temperature'],
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
    def get_supported_process_types() -> List[str]:
        """Retourne dynamiquement les types de procédés disponibles"""
        registry = ProcessRegistry.get_instance()
        return registry.get_process_types()
    
    @staticmethod
    def get_supported_model_types() -> List[str]:
        """Retourne dynamiquement les modèles disponibles dans le registre"""
        registry = ProcessRegistry.get_instance()
        return  list({definition.model for definition in registry.processes.values()})
    
    @staticmethod
    def is_valid_model_type(model_type: str) -> bool:
        """
        Vérifie si le type de modèle est supporté
        """
        return model_type.upper() in [m.upper() for m in ConfigSchema.get_supported_model_types()]
    
    @staticmethod
    def is_valid_process_type(process_type: str) -> bool:
        """
        Vérifie si le type de procédé est supporté
        """
        return process_type in ConfigSchema.get_supported_process_types()