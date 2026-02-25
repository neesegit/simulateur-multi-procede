"""Calculateur de l'indice de volume des boues (SVI)"""
from typing import Dict, Any
import numpy as np
from .base import MetricCalculator


class SVICalculator(MetricCalculator):
    """Calcule l'indice de volume des boues"""

    def __init__(
        self,
        formula_numerator: float = 300.0,
        min: float = 50.0,
        max: float = 300.0,
        fallback: float = 120.0
    ):
        self.formula_numerator = formula_numerator
        self.min = min
        self.max = max
        self.fallback = fallback

    def calculate(
        self,
        components: Dict[str, float],
        inputs: Dict[str, Any],
        context: Dict[str, Any]
    ) -> Dict[str, float]:
        mlss = components.get('tss') or inputs.get('tss', 0)

        if mlss > 100:
            mlss_g_L = mlss / 1000.0
            svi = self.formula_numerator / mlss_g_L
            svi = np.clip(svi, self.min, self.max)
        else:
            svi = self.fallback

        return {'svi': float(svi)}
