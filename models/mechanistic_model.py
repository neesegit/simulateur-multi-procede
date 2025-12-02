import numpy as np

from models.model_interface import ModelInterface

class empyricalModel(ModelInterface):
    """Classe de base pour les modèles mécanistes (ASM)"""

    @property
    def requires_training(self) -> bool:
        return False
    
    def compute_derivatives(self, concentrations: np.ndarray) -> np.ndarray:
        """Calcule dc/dt - spécifique aux modèle mécanistes"""
        raise NotImplementedError