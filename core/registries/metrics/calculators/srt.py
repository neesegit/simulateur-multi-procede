"""Calculateur du temps de rétention des solides (SRT)"""
from typing import Dict, Any
import numpy as np
from .base import MetricCalculator


class SRTCalculator(MetricCalculator):
    """Calcule le temps de rétention des solides"""

    def __init__(self, min_days: float = 3.0, max_days: float = 50.0, fallback_days: float = 20.0):
        self.min_days = min_days
        self.max_days = max_days
        self.fallback_days = fallback_days

    def calculate(
        self,
        components: Dict[str, float],
        inputs: Dict[str, Any],
        context: Dict[str, Any]
    ) -> Dict[str, float]:
        mlss = components.get('tss') or inputs.get('tss', 0)
        volume = context.get('volume', 0)
        flowrate = inputs.get('flowrate', 0)
        waste_ratio = context.get('waste_ratio', 0.01)

        if flowrate > 0 and mlss > 100:
            waste_flow = flowrate * waste_ratio
            total_solids_kg = mlss * volume / 1000.0
            wasted_solids_kg_per_day = waste_flow * mlss * 24 / 1000.0

            srt_days = total_solids_kg / wasted_solids_kg_per_day
            srt_days = np.clip(srt_days, self.min_days, self.max_days)
        else:
            srt_days = self.fallback_days

        return {'srt_days': float(srt_days)}
