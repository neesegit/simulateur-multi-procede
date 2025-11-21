from typing import List

from .activated_sludge_calibrator import ActivatedSludgeCalibrator

class ASM3Calibrator(ActivatedSludgeCalibrator):
    """Calibrateur spécifique pour ASM3"""
    def get_convergence_parameters(self) -> List[str]:
        """
        Retourne la lsite des paramètres à vérifier pour la convergence

        Returns:
            List[str]: Noms des paramètres
        """
        return [
            'so2',
            'snh4',
            'snox',
            'ss',
            'xs',
            'xh',
            'xa'
        ]
    
    def get_key_output_parameters(self) -> List[str]:
        """
        Retourne les paramètres clés à extraire

        Returns:
            List[str]: Noms des paramètres de sortie
        """
        return [
            'so2',
            'si',
            'ss',
            'snh4',
            'sn2',
            'snox',
            'salk',
            'xi',
            'xs',
            'xh',
            'xsto',
            'xa',
            'xss'
        ]