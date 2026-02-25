"""Classe de base abstraite pour les stratégies de fractionnement"""
from abc import ABC, abstractmethod
from typing import Dict


class FractionationStrategy(ABC):
    """Interface pour les stratégies de fractionnement"""

    @abstractmethod
    def fractionate(self, **kwargs) -> Dict[str, float]:
        """Fractionne les paramètres mesurés en composants du modèle"""
        pass

    @abstractmethod
    def get_required_inputs(self) -> list[str]:
        """Retourne la liste des inputs requis pour le fractionnement"""
        pass
