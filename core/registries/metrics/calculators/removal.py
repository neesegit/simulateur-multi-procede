"""Calculateur d'efficacité d'élimination"""
from typing import Dict, Any
from .base import MetricCalculator


class RemovalEfficiencyCalculator(MetricCalculator):
    """Calcule l'efficacité d'élimination"""

    def __init__(self, input_key: str, output_key: str):
        self.input_key = input_key
        self.output_key = output_key

    def calculate(
        self,
        components: Dict[str, float],
        inputs: Dict[str, Any],
        context: Dict[str, Any]
    ) -> Dict[str, float]:
        value_in = inputs.get(self.input_key, 0)
        value_out = components.get(self.output_key, 0)

        if value_in > 0:
            efficiency = max(0, (value_in - value_out) / value_in * 100)
            return {'efficiency': min(98.0, efficiency)}
        return {'efficiency': 0.0}
