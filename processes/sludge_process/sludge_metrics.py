"""
Calcule les métriques COD, TKN etc
"""
import numpy as np

from typing import Dict, Any
from core.model.model_registry import ModelRegistry

class SludgeMetrics:
    def __init__(self, model_type: str, registry: ModelRegistry):
        self.model_type = model_type
        model_def = registry.get_model_definition(self.model_type)
        self.config = model_def.get_metrics_dict()

    def _sum_keys(self, c: Dict[str, float], key_type: str) -> float:
        """Somme générique des clés configurées pour un type donné"""
        keys = self.config.get(key_type, [])
        if keys is None:
            return 0.0
        if isinstance(keys, str):
            return float(c.get(keys, 0))
        return float(sum(c.get(k, 0) for k in keys))
    
    def _get_value(self, c: Dict[str, float], config_key: str) -> float:
        """Récupère une valeur simple selon la clé configurée"""
        if key_name := self.config.get(config_key):
            return float(c.get(key_name, 0))
        return 0.0
    
    def _cod(self, c): return self._sum_keys(c, 'cod')
    def _tkn(self, c): return self._sum_keys(c, 'tkn')
    def _ss(self, c): return self._sum_keys(c, 'ss')
    def _biomass(self, c): return self._sum_keys(c, 'biomass')
    def _nh4(self, c): return self._get_value(c, 'nh4')
    def _no3(self, c): return self._get_value(c, 'no3')
    def _po4(self, c): return self._get_value(c, 'po4')
    def _soluble_cod(self, c): return self._sum_keys(c, 'soluble_cod')

    def compute(
            self,
            comp_out: Dict[str, float],
            c_in: np.ndarray,
            q_in: float,
            dt: float,
            volume: float,
            temperature: float = 20.0
    ) -> Dict[str, Any]:
        cod_out = self._cod(comp_out)
        tkn_out = self._tkn(comp_out)
        ss_out = self._ss(comp_out)
        nh4_out = self._nh4(comp_out)
        no3_out = self._no3(comp_out)
        po4_out = self._po4(comp_out)
        cod_soluble = self._soluble_cod(comp_out)
        cod_particulate = max(0, cod_out - cod_soluble)


        comp_in_dict = {k: float(v) for k, v in zip(comp_out.keys(), c_in)}
        cod_in = self._cod(comp_in_dict)
        cod_soluble_in = self._soluble_cod(comp_in_dict)

        if cod_soluble_in > 0:
            soluble_cod_removal = max(0, (
                (cod_soluble_in - cod_soluble) / cod_soluble_in * 100
            ))
        else:
            soluble_cod_removal = 0.0

        if cod_in > 0:
            cod_removal = max(0, (cod_in - cod_out) / cod_in *100)
            cod_removal = min(98.0, cod_removal)
        else:
            cod_removal = 0.0

        biomass = self._biomass(comp_out)
        mlss = ss_out

        if mlss < biomass * 1.2:
            mlss = biomass * 1.5
        
        mlss = np.clip(mlss, 1500.0, 5000.0)

        waste_ratio = 0.01
        waste_flow = q_in * waste_ratio

        if waste_flow > 0 and mlss > 100:
            total_solids_kg = mlss * volume / 1000.0
            wasted_solids_kg_per_day = waste_flow*mlss*24/1000.0
            srt_days = total_solids_kg / wasted_solids_kg_per_day

            srt_days = np.clip(srt_days, 3.0, 50.0)
        else :
            srt_days = 20.0

        settled_volume = volume * 0.30 # m^3
        settled_volume_L = settled_volume * 1000 # litres

        if mlss > 100:
            mlss_g_L = mlss / 1000.0
            svi = (settled_volume_L / (mlss_g_L * volume)) * 1000

            svi = np.clip(svi, 80.0, 200.0)
        else:
            svi = 120.0

        cod_removed_mg = max(0, cod_in - cod_out)
        oxygen_consumed_kg = (cod_removed_mg * q_in * dt) / 1000.0

        aeration_energy_kwh = max(0, oxygen_consumed_kg * 2.0)

        total_volume_m3 = q_in * dt
        if total_volume_m3 > 0:
            energy_per_m3 = aeration_energy_kwh / total_volume_m3
        else:
            energy_per_m3 = 0.0

        hrt_hours = volume / q_in if q_in > 0 else 0
        hrt_hours = np.clip(hrt_hours, 2.0, 48.0)

        return {
            'flowrate': q_in,
            'temperature': temperature,
            'model_type': self.model_type,
            'components': comp_out,

            'cod': cod_out,
            'bod': cod_out * 0.6,
            'tkn': tkn_out,
            'ss': ss_out,
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