"""
Calcule les métriques COD, TKN etc
"""
import numpy as np
import logging

from typing import Dict, Any
from core.model.model_registry import ModelRegistry
from core.registries.metrics_registry import MetricsRegistry, create_composite_calculator

logger = logging.getLogger(__name__)

class SludgeMetrics:
    def __init__(self, model_type: str, model_registry: ModelRegistry):
        self.model_type = model_type
        self.metrics_registry = MetricsRegistry.get_instance()

        model_def = model_registry.get_model_definition(self.model_type)

        self._setup_composite_calculators(model_def)

    def _setup_composite_calculators(self, model_def):
        """Configure les calculateurs composites basés sur la définition du modèle"""
        self.cod_calculator = create_composite_calculator(model_def, 'cod')
        self.tkn_calculator = create_composite_calculator(model_def, 'tkn')
        self.tss_calculator = create_composite_calculator(model_def, 'tss')
        self.biomass_calculator = create_composite_calculator(model_def, 'biomass')

        metrics_dict = model_def.get_metrics_dict()
        self.nh4_key = metrics_dict.get('nh4')
        self.no3_key = metrics_dict.get('no3')
        self.po4_key = metrics_dict.get('po4')
        self.soluble_cod_key = metrics_dict.get('soluble_cod', [])
        if isinstance(self.soluble_cod_key, str):
            self.soluble_cod_key = [self.soluble_cod_key]
    
    def _get_value(self, components: Dict[str, float], key: str) -> float:
        """Récupère une valeur simple"""
        if key:
            return float(components.get(key, 0))
        return 0.0

    def compute(
            self,
            comp_out: Dict[str, float],
            c_in: np.ndarray,
            q_in: float,
            dt: float,
            volume: float,
            temperature: float = 20.0
    ) -> Dict[str, Any]:
        """Calcule toutes les métriques pour un pas de temps"""
        cod_out = self.cod_calculator.calculate(comp_out, {}, {})['value'] if self.cod_calculator else 0
        tkn_out = self.tkn_calculator.calculate(comp_out, {}, {})['value'] if self.tkn_calculator else 0
        tss_out = self.tss_calculator.calculate(comp_out, {}, {})['value'] if self.tss_calculator else 0
        biomass = self.biomass_calculator.calculate(comp_out, {}, {})['value'] if self.biomass_calculator else 0

        nh4_out = self._get_value(comp_out, self.nh4_key)
        no3_out = self._get_value(comp_out, self.no3_key)
        po4_out = self._get_value(comp_out, self.po4_key)

        cod_soluble = sum(comp_out.get(k, 0) for k in self.soluble_cod_key)
        cod_particulate = max(0, cod_out - cod_soluble)

        comp_in_dict = {k: float(v) for k, v in zip(comp_out.keys(), c_in)}
        cod_in = self.cod_calculator.calculate(comp_in_dict, {}, {})['value'] if self.cod_calculator else 0
        cod_soluble_in = sum(comp_in_dict.get(k, 0) for k in self.soluble_cod_key)

        if cod_soluble_in > 0:
            soluble_cod_removal = max(0, (
                (cod_soluble_in - cod_soluble) / cod_soluble_in * 100
            ))
        else:
            soluble_cod_removal = 0.0

        if cod_in > 0:
            cod_removal = max(0, (cod_in - cod_out) / cod_in * 100)
            cod_removal = min(98.0, cod_removal)
        else:
            cod_removal = 0.0

        mlss = tss_out
        if mlss < biomass * 1.2:
            mlss = biomass * 1.5
        mlss = np.clip(mlss, 1500.0, 5000.0)

        context = {
            'volume': volume,
            'waste_ratio': 0.01,
            'temperature': temperature
        }

        inputs = {
            'flowrate': q_in,
            'cod_in': cod_in,
            'cod_out': cod_out
        }

        hrt_result = self.metrics_registry.calculate('hrt', comp_out, inputs, context)
        srt_result = self.metrics_registry.calculate('srt', comp_out, inputs, context)
        svi_result = self.metrics_registry.calculate('svi', comp_out, inputs, context)
        energy_result = self.metrics_registry.calculate('energy', comp_out, inputs, context)

        hrt_hours = hrt_result.get('hrt_hours', 0)
        srt_days = srt_result.get('srt_days', 20.0)
        svi = svi_result.get('svi', 120.0)

        oxygen_consumed_kg = energy_result.get('oxygen_consumed_kg', 0)
        aeration_energy_kwh = energy_result.get('aeration_energy_kwh', 0)
        energy_per_m3 = energy_result.get('energy_per_m3', 0)

        return {
            'flowrate': q_in,
            'temperature': temperature,
            'model_type': self.model_type,
            'components': comp_out,

            'cod': cod_out,
            'bod': cod_out * 0.6,
            'tkn': tkn_out,
            'tss': tss_out,
            'nh4': nh4_out,
            'no3': no3_out,
            'po4': po4_out,
            'cod_soluble': cod_soluble,
            'cod_particulate': cod_particulate,

            'cod_removal_rate': cod_removal,
            'soluble_cod_removal': soluble_cod_removal,

            'hrt_hours': hrt_hours,
            'srt_days': srt_days,
            'svi': svi,
            'mlss': mlss,
            'biomass_concentration': biomass,

            'oxygen_consumed_kg': oxygen_consumed_kg,
            'aeration_energy_kwh': aeration_energy_kwh,
            'energy_per_m3': energy_per_m3,

            '_data_quality': {
                'svi_realistic': 80 <= svi <= 200,
                'srt_realistic': 5 <= srt_days <= 30,
                'mlss_realistic': 1500 <= mlss <= 4500,
                'cod_removal_realistic': 70 <= cod_removal <= 98,
                'energy_positive': aeration_energy_kwh >= 0
            }
        }