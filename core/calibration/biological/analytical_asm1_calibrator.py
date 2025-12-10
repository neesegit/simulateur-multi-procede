import numpy as np

from typing import List

from core.calibration.analytical_calibrator import AnalyticalCalibrator
from models.empyrical.asm1.model import ASM1Model 

class AnalyticalASM1Calibrator(AnalyticalCalibrator):
    """Calibrateur analytique pour ASM1"""

    def get_convergence_parameters(self) -> List[str]:
        return ['so', 'snh', 'sno', 'ss', 'xbh', 'xba']
    
    def get_key_output_parameters(self) -> List[str]:
        return [
            'so', 'snh', 'sno', 'ss', 'xbh', 'xba', 'si', 'xi', 'xs', 'xp', 'snd', 'xnd', 'salk'
        ]
    
    def _physical_guess(
            self,
            model: ASM1Model, 
            c_in: np.ndarray, 
            hrt_days: float, 
            srt_days: float, 
            substrate_reduction: float
    ) -> np.ndarray:
        """
        Estimation physique pour ASM1
        """
        c0 = c_in.copy()
        idx = model.COMPONENT_INDICES

        c0[idx['ss']] *= substrate_reduction
        c0[idx['xs']] *= 0.5

        ss_in = c_in[idx['ss']]
        xs_in = c_in[idx['xs']]
        cod_biodegradable_in = ss_in + xs_in

        yield_h = 0.67
        xbh_estimate = yield_h * cod_biodegradable_in * (srt_days / hrt_days)

        c0[idx['xbh']] = np.clip(xbh_estimate, 1500.0, 4000.0)

        c0[idx['xba']] = c0[idx['xbh']] * 0.10

        c0[idx['snh']] = c_in[idx['snh']] * 0.1

        nh4_nitrified = c_in[idx['snh']] * 0.9
        c0[idx['sno']] = c_in[idx['sno']] + nh4_nitrified * 0.7

        c0[idx['snd']] = c_in[idx['snd']] * 0.5
        c0[idx['xnd']] = c_in[idx['xnd']] * 0.7

        do_setpoint = self.process_config.get('config', {}).get('dissolved_oxygen_setpoint', 2.0)
        c0[idx['so']] = do_setpoint

        alk_consumed = nh4_nitrified * (7.14/50000)
        c0[idx['salk']] = max(c_in[idx['salk']] - alk_consumed, 2.0)

        c0[idx['xp']] = c_in[idx.get('xp', 6)] * 1.2

        print(f"\tXBH estimé : {c0[idx['xbh']]:.1f} mg COD/L")
        print(f"\tXBA estimé : {c0[idx['xba']]:.1f} mg COD/L")

        return c0