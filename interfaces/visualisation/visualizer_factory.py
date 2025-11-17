"""
Factory pour instancier le bon visualiseur selon le modèle
"""
import logging
import importlib

from typing import Optional
from core.model.model_registry import ModelRegistry
from .base.base_visualizer import BaseVisualizer

logger = logging.getLogger(__name__)

class VisualizerFactory:
    """Factory pour créer les visualiseurs appropriés"""

    @staticmethod
    def create(model_type: str) -> Optional[BaseVisualizer]:
        """Crée un visualiseur pour le type de modèle donnée"""
        model_type = model_type.strip()
        if not model_type.endswith('Model'):
            model_type += 'Model'
        
        short = model_type.replace('Model', '').lower()

        module_path = f"interfaces.visualisation.models.{short}_visualizer"
        class_name = f"{short.upper()}Visualizer"

        visualizer_class = None
        
        try:
            module = importlib.import_module(module_path)
            visualizer_class = getattr(module, class_name)

        except ModuleNotFoundError:
            logger.warning(f'Aucun module visualiseur trouvé pour {model_type}')
            return None
        
        except AttributeError:
            logger.error(f"Classe visualiseur '{class_name}' absente dans {module_path}")
        
        if visualizer_class is None:
            logger.error(f"Visualiseur introuvable pour {model_type}")
            return None

        registry = ModelRegistry.get_instance()
        model_def = registry.get_model_definition(model_type)


        visualizer = visualizer_class(model_type, model_def)
        logger.info(f"Visualizer {visualizer_class.__name__} crée pour {model_type}")

        return visualizer