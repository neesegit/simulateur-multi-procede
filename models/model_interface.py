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

    @abstractmethod
    def predict_step(
        self,
        current_state: Dict[str, float],
        inputs: Dict[str, float],
        dt: float
    ) -> Dict[str, float]:
        """
        Prédit l'état au prochain pas de temps

        Args:
            current_state (Dict[str, float]): Etat actual du système
            inputs (Dict[str, float]): Entrées (débit, température, etc)
            dt (float): Pas de temps

        Returns:
            Dict[str, float]: Dict avec les prédictions des composants
        """
        pass

    @abstractmethod
    def initialize_state(self, initial_conditions: Dict[str, float]) -> Dict[str, float]:
        """Initialise l'état du modèle"""
        pass

    @property
    @abstractmethod
    def model_type(self) -> str:
        """Type du modèle (asm1, rnn, linear, etc)"""
        pass

    @property
    def requires_training(self) -> bool:
        """Indique si le modèle nécessite un entraînement"""
        return False