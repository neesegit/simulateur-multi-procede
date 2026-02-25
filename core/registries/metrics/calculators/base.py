"""Classe de base abstraite pour les calculateurs de métriques"""
from typing import Dict, Any
from abc import ABC, abstractmethod


class MetricCalculator(ABC):
    """Interface pour les calculateurs de métriques"""

    @abstractmethod
    def calculate(
        self,
        components: Dict[str, float],
        inputs: Dict[str, Any],
        context: Dict[str, Any]
    ) -> Dict[str, float]:
        """Calcule les métriques"""
        pass
