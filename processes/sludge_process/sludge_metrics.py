"""
Calcule les métriques COD, TKN etc
"""

import numpy as np

from typing import Dict, Any

class SludgeMetrics:
    def __init__(self, model_name: str):
        self.model_name = model_name.upper()

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
            'model_type': self.model_name,
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

    def _cod(self, c: Dict[str, float]) -> float:
        if self.model_name == 'ASM1':
            keys = ['si', 'ss', 'xi', 'xs', 'xbh', 'xba', 'xp']
        elif self.model_name == 'ASM2D':
            keys = ['so2', 'sf', 'sa', 'xi', 'xs', 'xh', 'xaut', 'xpao', 'xpp', 'xpha', 'xmeoh', 'xmep']
        else:
            keys = []
        return float(sum(c.get(k, 0) for k in keys))
    
    def _tkn(self, c: Dict[str, float]) -> float:
        if self.model_name == 'ASM1':
            keys = ['snh', 'snd', 'xnd']
        elif self.model_name == 'ASM2D':
            keys = ['snh4', 'xi', 'xs', 'xh', 'xpao', 'xaut']
        else:
            keys = []
        return float(sum(c.get(k, 0) for k in keys))
    
    def _ss(self, c: Dict[str, float]) -> float:
        if self.model_name == 'ASM1':
            keys = ['xi', 'xs', 'xbh', 'xba', 'xp']
        elif self.model_name == 'ASM2D':
            keys = ['xi', 'xs', 'xh', 'xpao', 'xpp', 'xpha', 'xaut', 'xmeoh', 'xmep']
        else:
            keys = []
        return float(sum(c.get(k, 0) for k in keys))
    
    def _biomass(self, c: Dict[str, float]) -> float:
        if self.model_name == 'ASM1':
            keys = ['xbh', 'xba']
        elif self.model_name == 'ASM2D':
            keys = ['xh', 'xaut', 'xpao']
        else:
            keys = []
        return float(sum(c.get(k, 0) for k in keys))
    
    def _nh4(self, c: Dict[str, float]) -> float:
        if self.model_name == 'ASM1':
            return float(c.get('snh', 0))
        elif self.model_name == 'ASM2D':
            return float(c.get('snh4', 0))
        return 0.0

    def _no3(self, c: Dict[str, float]) -> float:
        if self.model_name == 'ASM1':
            return float(c.get('sno', 0))
        elif self.model_name == 'ASM2D':
            return float(c.get('sno3', 0))
        return 0.0

    def _po4(self, c: Dict[str, float]) -> float:
        if self.model_name == 'ASM1':
            return 0.0
        elif self.model_name == 'ASM2D':
            return float(c.get('spo4', 0.0))
        return 0.0
    
    def _soluble_cod(self, c: Dict[str, float]) -> float:
        if self.model_name == 'ASM1':
            return float(c.get('ss', 0))
        elif self.model_name == 'ASM2D':
            return float(c.get('sf', 0) + c.get('sa', 0))
        return 0.0
