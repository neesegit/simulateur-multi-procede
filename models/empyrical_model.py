import numpy as np

from abc import abstractmethod
from models.model_interface import ModelInterface

class EmpyricalModel(ModelInterface):
    """Classe de base pour les modèles mécanistes (ASM)"""

    @property
    def requires_training(self) -> bool:
        return False
    
    @property
    @abstractmethod
    def model_type(self) -> str:
        """Type du modèle (asm1, linear, etc)"""
        pass
    
    def compute_derivatives(self, concentrations: np.ndarray) -> np.ndarray:
        """Calcule dc/dt - spécifique aux modèle mécanistes"""
        raise NotImplementedError