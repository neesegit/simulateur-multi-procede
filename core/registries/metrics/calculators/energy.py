"""Calculateur de consommation énergétique"""
from typing import Dict, Any
from .base import MetricCalculator


class EnergyConsumptionCalculator(MetricCalculator):
    """Calcule la consommation énergétique"""

    def calculate(
        self,
        components: Dict[str, float],
        inputs: Dict[str, Any],
        context: Dict[str, Any]
    ) -> Dict[str, float]:
        cod_in = inputs.get('cod_soluble_in', inputs.get('cod_in', 0))
        cod_out = inputs.get('cod_soluble_out', inputs.get('cod_out', 0))
        flowrate = inputs.get('flowrate', 0)
        dt = context.get('dt', 0)

        cod_removed_mg = max(0, cod_in - cod_out)
        oxygen_consumed_kg = (cod_removed_mg * flowrate * dt) / 1000.0
        aeration_energy_kwh = max(0, oxygen_consumed_kg * 2.0)

        total_volume_m3 = flowrate * dt
        energy_per_m3 = aeration_energy_kwh / total_volume_m3 if total_volume_m3 > 0 else 0

        return {
            'oxygen_consumed_kg': oxygen_consumed_kg,
            'aeration_energy_kwh': aeration_energy_kwh,
            'energy_per_m3': energy_per_m3
        }
