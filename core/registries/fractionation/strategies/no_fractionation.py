"""Stratégie de fractionnement nulle (pass-through)"""
from typing import Dict
from .base import FractionationStrategy


class NoFractionationStrategy(FractionationStrategy):
    """Stratégie pour les modèles qui ne nécessitent pas de fractionnement"""

    def fractionate(self, **kwargs) -> Dict[str, float]:
        return kwargs.get('components', {})

    def get_required_inputs(self) -> list[str]:
        return []
