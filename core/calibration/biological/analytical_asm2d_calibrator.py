import numpy as np

from typing import List

from core.calibration.analytical_calibrator import AnalyticalCalibrator
from models.empyrical.asm2d.model import ASM2dModel

class AnalyticalASM2DCalibrator(AnalyticalCalibrator):
    """Calibrateur analytique pour ASM2d"""

    def get_convergence_parameters(self) -> List[str]:
        return [
            'so2', 'snh4', 'sno3', 'spo4', 'sf', 'sa', 'xh', 'xpao', 'xaut', 'xpha', 'xpp'
        ]
    
    def get_key_output_parameters(self) -> List[str]:
        return [
            'so2', 'sf', 'sa', 'si', 'snh4', 'sno3', 'sn2', 'spo4', 'salk',
            'xi', 'xs', 'xh', 'xpao', 'xpp', 'xpha', 'xaut', 'xtss', 'xmeoh', 'xmep'
        ]
    
    def _physical_guess(
            self, 
            model: ASM2dModel, 
            c_in: np.ndarray, 
            hrt_days: float, 
            srt_days: float, 
            substrate_reduction: float
    ) -> np.ndarray:
        """Estimation physique pour ASM2d"""
        c0 = c_in.copy()
        idx = model.COMPONENT_INDICES

        c0[idx['sf']] *= substrate_reduction
        c0[idx['sa']] *= substrate_reduction
        c0[idx['xs']] *= 0.5

        sf_in = c_in[idx['sf']]
        sa_in = c_in[idx['sa']]
        xs_in = c_in[idx['xs']]
        cod_biodegradable = sf_in + sa_in + xs_in

        yield_h = 0.625
        biomass_total = yield_h * cod_biodegradable * (srt_days / hrt_days)
        biomass_total = np.clip(biomass_total, 1500.0, 4000.0)

        c0[idx['xh']] = biomass_total * 0.80
        c0[idx['xpao']] = biomass_total * 0.10
        c0[idx['xaut']] = biomass_total * 0.05

        c0[idx['xpha']] = c0[idx['xpao']] * 0.05
        c0[idx['xpp']] = c0[idx['xpao']] * 0.25

        c0[idx['snh4']] = c_in[idx['snh4']] * 0.1
        nh4_nitrified = c_in[idx['snh4']] * 0.9
        c0[idx['sno3']] = c_in[idx['sno3']] + nh4_nitrified * 0.7

        c0[idx['spo4']] = c_in[idx['spo4']] * 0.2

        do_setpoint = self.process_config.get('config', {}).get('dissolved_oxygen_setpoint', 2.0)
        c0[idx['so2']] = do_setpoint

        c0[idx['xtss']] = biomass_total * 0.9

        print(f"\tBiomasse totale : {biomass_total:.1f} mg COD/L")
        print(f"\tXH={c0[idx['xh']]:.0f}, XPAO={c0[idx['xpao']]:.0f}, XAUT={c0[idx['xaut']]:.0f} mg COD/L")

        return c0