from typing import List

from .activated_sludge_calibrator import ActivatedSludgeCalibrator

class ASM1Calibrator(ActivatedSludgeCalibrator):
    """Calibrateur spécifique pour ASM1"""
    
    def get_convergence_parameters(self) -> List[str]:
        """
        Retourne la lsite des paramètres à vérifier pour la convergence

        Returns:
            List[str]: Noms des paramètres
        """
        return [
            'so',
            'snh',
            'sno',
            'ss',
            'xbh',
            'xba'
        ]

    
    def get_key_output_parameters(self) -> List[str]:
        """
        Retourne les paramètres clés à extraire

        Returns:
            List[str]: Noms des paramètres de sortie
        """
        return [
            'so',
            'snh',
            'sno',
            'ss',
            'xbh',
            'xba',
            'si',
            'xi',
            'xs',
            'xp',
            'snd',
            'xnd',
            'salk'
        ]