import numpy as np

from typing import Dict
from abc import abstractmethod
from models.model_interface import ModelInterface

class DynamicModel(ModelInterface):
    """Mdoèle continus décrits par des EDO"""
    
    @abstractmethod
    def derivatives(self, state: np.ndarray) -> np.ndarray:
        """
        Calcule les dérivées dX/dt

        Args:
            state (np.ndarray): Vecteur d'état actuel (concentrations, etc.)

        Returns:
            np.ndarray: Dérivées dX/dt
        """
        pass

    @abstractmethod
    def dict_to_concentrations(self, state_dict: Dict[str, float]) -> np.ndarray:
        """Convertit un dictionnaire d'état en vecteur numpy"""
        pass

    @abstractmethod
    def concentrations_to_dict(self, state: np.ndarray) -> Dict[str, float]:
        """Convertit un vecteur numpy en dictionnaire d'état"""
        pass