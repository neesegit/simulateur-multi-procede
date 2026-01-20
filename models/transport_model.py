import numpy as np

from abc import abstractmethod
from models.dynamic_model import DynamicModel

class TransportModel(DynamicModel):
    """
    Modèles de transport / flux / sédimentation
    """

    @abstractmethod
    def compute_fluxes(
        self,
        state: np.ndarray,
        velocities: np.ndarray
    ) -> np.ndarray:
        """
        Calcule les flux entre couches / compartiments

        Args:
            state (np.ndarray): Etat actuel (concentrations par couche)
            velocities (np.ndarray): Vitesses d'écoulement / sédimentation

        Returns:
            np.ndarray: Flux entre compartiments
        """
        pass

    @abstractmethod
    def compute_settling_velocity(self, X: np.ndarray) -> np.ndarray:
        """
        Calcule les vitesses de sédimentation (pour modèles de décantation)

        Args:
            X (np.ndarray): Concentrations dans chaque couche

        Returns:
            np.ndarray: Vitesses de sédimentation par couche
        """
        pass