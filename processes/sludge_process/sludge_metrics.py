"""
Calcule les métriques COD, TKN etc
"""

import numpy as np

from typing import Dict, Any

class SludgeMetrics:
    def __init__(self, model_name: str):
        self.model_name = model_name

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

        cod_in = self._cod({k: float(v) for k, v in zip(comp_out.keys(), c_in)})
        cod_removal = ((cod_in - cod_out) / cod_in*100) if cod_in > 0 else 0
        oxygen_consumed = (cod_in - cod_out) * q_in * dt / 1000.0
        energy = oxygen_consumed * 2.0

        return {
            'flowrate': q_in,
            'temperature': temperature,
            'model_type': self.model_name,
            'components': comp_out,

            'cod': cod_out,
            'tkn': tkn_out,
            'ss': ss_out,
            'bod': cod_out * 0.6,
            'cod_removal_rate': cod_removal,
            'hrt_hours': volume / q_in,
            'biomass_concentration': self._biomass(comp_out),

            'oxygen_consumed_kg': oxygen_consumed,
            'aeration_energy_kwh': energy,
            'energy_per_m^3': energy / (q_in * dt) if q_in > 0 else 0
        }

    def _cod(self, c: Dict[str, float]) -> float:
        return sum(c.get(k, 0) for k in ['si', 'ss', 'xi', 'xs', 'xbh', 'xba', 'xp'])
    
    def _tkn(self, c: Dict[str, float]) -> float:
        return sum(c.get(k, 0) for k in ['snh', 'snd', 'xnd'])
    
    def _ss(self, c: Dict[str, float]) -> float:
        return sum(c.get(k, 0) for k in ['xi', 'xs', 'xbh', 'xba', 'xp'])
    
    def _biomass(self, c: Dict[str, float]) -> float:
        return sum(c.get(k, 0) for k in ['xbh', 'xba'])