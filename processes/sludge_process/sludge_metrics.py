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
        cod_particulate = cod_out - cod_soluble


        cod_in = self._cod({k: float(v) for k, v in zip(comp_out.keys(), c_in)})
        cod_soluble_in = self._soluble_cod({k: float(v) for k, v in zip(comp_out.keys(), c_in)})

        if cod_soluble_in > 0:
            soluble_cod_removal = (
                (cod_soluble_in - cod_soluble) / cod_soluble_in * 100
            )
        else:
            soluble_cod_removal = 0.0

        mlss = ss_out
        waste_flow = q_in*0.01
        if waste_flow > 0:
            total_solids_kg = mlss * volume / 1000
            wasted_solids_kg_per_day = waste_flow*mlss*24/1000
            srt_days = total_solids_kg / wasted_solids_kg_per_day if wasted_solids_kg_per_day > 0 else 0
        else :
            srt_days = float('inf')

        svi = (volume / mlss)*1000 if mlss > 100 else 0

        cod_removal = ((cod_in - cod_out) / cod_in*100) if cod_in > 0 else 0
        oxygen_consumed = (cod_in - cod_out) * q_in * dt / 1000.0
        energy = oxygen_consumed * 2.0

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
            'hrt_hours': volume / q_in,
            'srt_days': srt_days,
            'svi': svi,
            'biomass_concentration': self._biomass(comp_out),

            'oxygen_consumed_kg': oxygen_consumed,
            'aeration_energy_kwh': energy,
            'energy_per_m3': energy / (q_in * dt) if q_in > 0 else 0
        }