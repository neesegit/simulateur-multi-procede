"""
Interface commune pour tous les types de modèles
"""
import numpy as np

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional

class ModelInterface(ABC):
    """Interface que tous les modèles doivent implémenter"""

    def __init__(self, params: Optional[Dict[str, Any]] = None):
        self.params = params or {}
        self.is_fitted = False

    @abstractmethod
    def get_component_names(self) -> List[str]:
        """Retourne les noms des composants/features"""
        pass

    @property
    @abstractmethod
    def model_type(self) -> str:
        """Type du modèle (asm1, linear, etc)"""
        pass

    @property
    def requires_training(self) -> bool:
        """Indique si le modèle nécessite un entraînement"""
        return False