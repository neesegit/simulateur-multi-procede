import numpy as np

from typing import List

from core.calibration.analytical_calibrator import AnalyticalCalibrator
from models.empyrical.asm3.model import ASM3Model

class AnalyticalASM3Calibrator(AnalyticalCalibrator):
    """Calibrateur analytique pour ASM3"""

    def get_convergence_parameters(self) -> List[str]:
        return ['so2', 'snh4', 'snox', 'ss', 'xs', 'xh', 'xa']
    
    def get_key_output_parameters(self) -> List[str]:
        return [
            'so2', 'si', 'ss', 'snh4', 'sn2', 'snox', 'salk',
            'xi', 'xs', 'xh', 'xsto', 'xa', 'xss'
        ]
    
    def _physical_guess(
            self, 
            model: ASM3Model, 
            c_in: np.ndarray, 
            hrt_days: float, 
            srt_days: float, 
            substrate_reduction: float
    ) -> np.ndarray:
        """Estimation physique pour ASM3"""
        c0 = c_in.copy()
        idx = model.COMPONENT_INDICES

        c0[idx['ss']] *= substrate_reduction
        c0[idx['xs']] *= 0.5

        ss_in = c_in[idx['ss']]
        xs_in = c_in[idx['xs']]
        cod_biodegradable = ss_in + xs_in

        yield_h = 0.63
        biomass_total = yield_h * cod_biodegradable * (srt_days / hrt_days)
        biomass_total = np.clip(biomass_total, 1500.0, 4000.0)

        c0[idx['xh']] = biomass_total * 0.90
        c0[idx['xa']] = biomass_total * 0.05
        c0[idx['xsto']] = biomass_total * 0.05

        c0[idx['snh4']] = c_in[idx['snh4']] * 0.1
        nh4_nitrified = c_in[idx['snh4']] * 0.9
        c0[idx['snox']] = c_in[idx['snox']] + nh4_nitrified * 0.7

        do_setpoint = self.process_config.get('config', {}).get('dissolved_oxygen_setpoint', 2.0)
        c0[idx['so2']] = do_setpoint

        c0[idx['xss']] = biomass_total * 0.9

        print(f"\tBiomasse totale : {biomass_total:.1f} mg COD/L")
        print(f"\tXH={c0[idx['xh']]:.0f}, XA={c0[idx['xa']]:.0f} mg COD/L")

        return c0