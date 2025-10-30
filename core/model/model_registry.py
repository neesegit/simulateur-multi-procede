"""
Registre centralisé des models disponibles

Ce module charge dynamiquement les procédés depuis un fichier json et gère leur instanciation
"""
import json
import logging

from pathlib import Path
from typing import Dict, Any, List, Optional, Type

from core.model.model_definition import ModelDefinition

logger = logging.getLogger(__name__)

class ModelRegistry:
    _instance = None

    def __init__(self, catalog_path: Optional[Path]) -> None:
        if catalog_path is None:
            catalog_path = Path(__file__).parent / 'config' / 'models_catalog.json'

        self.catalog_path = catalog_path
        self.models: Dict[str, ModelDefinition] = {}
        self.categories: Dict[str, Dict[str, str]] = {}

        self._load_catalog()

    def _load_catalog(self) -> None:
        """Charge le catalogue depuis le fichier json"""
        if not self.catalog_path.exists():
            raise FileNotFoundError(
                f"Catalogue de modèles introuvable : {self.catalog_path}"
            )
        
        with open(self.catalog_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        self.categories = data.get('categories', {})

        for model_data in data.get('models', []):
            definition = ModelDefinition.from_dict(model_data)
            self.models[definition.type] = definition
            logger.debug(f"Modèle chargé : {definition.type} - {definition.name}")

        logger.debug(f"Catalogue chargé : {len(self.models)} modèle(s)")

    @classmethod
    def get_instance(cls, catalog_path: Optional[Path] = None) -> 'ModelRegistry':
        """Retourne l'instance du registre"""
        if cls._instance is None:
            cls._instance = cls(catalog_path)
        return cls._instance
    
    def get_model_definition(self, model_type: str) -> ModelDefinition:
        """Récupère la définition d'un modèle"""
        if model_type not in self.models:
            available = ', '.join(self.models.keys())
            raise ValueError(
                f"Type de modèle inconnu : '{model_type}'. "
                f"Type disponibles : {available}"
            )
        return self.models[model_type]
    
    def create_model(
            self,
            model_type: str,
            **kwargs
    ) -> Any:
        """
        Crée une instance de modèle

        Args:
            model_type (str): Type du modèle
            **kwargs: Arguments à passer au constructeur du modèle

        Returns:
            Instance du modèle
        """
        definition = self.get_model_definition(model_type)
        model_class = definition.get_class()

        default_params = definition.get_default_params()
        if 'params' in kwargs:
            merged_params = default_params.copy()
            merged_params.update(kwargs['params'])
            kwargs['params'] = merged_params
        else:
            kwargs['params'] = default_params

        instance = model_class(**kwargs)
        logger.info(f"Modèle instancié : {definition.name} ({model_type})")
        return instance
    
    def list_models(self) -> List[ModelDefinition]:
        models = list(self.models.values())
        return sorted(models, key=lambda m: m.name)
    
    def get_model_types(self) -> List[str]:
        """Retourne la lsite des types de modèles disponibles"""
        return list(self.models.keys())
    
    def to_cli_format(self) -> Dict[str, Dict[str, Any]]:
        """
        Convertit le registre au format attendu par CLIInterface

        Returns:
            Dict[str, Dict[str, Any]]: Dict compabile avec l'affichage CLI
        """
        cli_format = {}

        for i, (model_type, definition) in enumerate(self.models.items(), 1):
            cli_format[str(i)] = {
                'type': definition.type,
                'name': definition.name,
                'description': definition.description,
                'parameters': [
                    {
                        'id': p.id,
                        'label': p.label,
                        'unit': p.unit,
                        'default': p.default
                    }
                    for p in definition.parameters
                ],
                'components': definition.components
            }
        return cli_format
    