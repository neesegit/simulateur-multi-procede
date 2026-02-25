"""Calculateur du temps de rétention hydraulique (HRT)"""
from typing import Dict, Any
import numpy as np
from .base import MetricCalculator


class HRTCalculator(MetricCalculator):
    """Calcule le temps de rétention hydraulique"""

    def __init__(self, min_hours: float = 2.0, max_hours: float = 48.0):
        self.min_hours = min_hours
        self.max_hours = max_hours

    def calculate(
        self,
        components: Dict[str, float],
        inputs: Dict[str, Any],
        context: Dict[str, Any]
    ) -> Dict[str, float]:
        volume = context.get('volume', 0)
        flowrate = inputs.get('flowrate', 0)

        hrt_hours = volume / flowrate if flowrate > 0 else 0
        hrt_hours = np.clip(hrt_hours, self.min_hours, self.max_hours)

        return {'hrt_hours': float(hrt_hours)}
