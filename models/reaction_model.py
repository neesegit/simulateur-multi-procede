import numpy as np

from abc import abstractmethod
from models.dynamic_model import DynamicModel

class ReactionModel(DynamicModel):
    """
    Modèles basés sur des réaction locales
    """

    @abstractmethod
    def process_rates(self, concentrations: np.ndarray) -> np.ndarray:
        """rho(X)"""
        pass

    @abstractmethod
    def stoichiometric_matrix(self) -> np.ndarray:
        """S (processus x composants)"""
        pass

    def derivatives(self, state: np.ndarray) -> np.ndarray:
        rho = self.process_rates(state)
        S = self.stoichiometric_matrix()
        return S.T @ rho