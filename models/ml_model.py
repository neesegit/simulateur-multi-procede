import numpy as np

from models.model_interface import ModelInterface

from typing import Dict, Any, Optional
from abc import abstractmethod

class MLModel(ModelInterface):
    """Classe de base pour les modèles ML"""

    def __init__(self, params: Optional[Dict[str, Any]] = None):
        super().__init__(params)
        self.scaler = None
        self.feature_names = []
        self.target_names = []
        self.sequence_buffer = []
        self.sequence_length = self.params.get('sequence_length', 7)

    @property
    def requires_training(self) -> bool:
        return True
    
    @abstractmethod
    def fit(self, X: np.ndarray, y: np.ndarray) -> dict:
        """Entraîne le modèle"""
        pass

    @abstractmethod
    def save(self, path: str) -> None:
        """Saubegarde le modèle"""
        pass

    @abstractmethod
    def load(self, path: str) -> None:
        """Charge un modèle pré-entrainé"""
        pass

    def _extract_features(
            self,
            current_state: Dict[str, float],
            inputs: Dict[str, float]
    ) -> np.ndarray:
        """Extrait les features depuis l'état et les inputs"""
        features = {}
        features.update(current_state)
        features.update(inputs)

        return np.array([features.get(name, 0.0) for name in self.feature_names])
    
    def update_buffer(self, features: np.ndarray) -> None:
        """Met à jour le buffer de séquences (pour RNN)"""
        if hasattr(self, 'sequence_length'):
            self.sequence_buffer.append(features)
            if len(self.sequence_buffer) > self.sequence_length:
                self.sequence_buffer.pop(0)

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