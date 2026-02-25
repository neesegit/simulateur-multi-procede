"""Calculateur composite : somme de plusieurs composants"""
from typing import Dict, Any
from .base import MetricCalculator


class CompositeMetricCalculator(MetricCalculator):
    """Calculateur qui combine plusieurs composants"""

    def __init__(self, component_names: list[str]):
        self.component_names = component_names

    def calculate(
        self,
        components: Dict[str, float],
        inputs: Dict[str, Any],
        context: Dict[str, Any]
    ) -> Dict[str, float]:
        return {
            'value': sum(components.get(name, 0.0) for name in self.component_names)
        }
