from typing import List

from .activated_sludge_calibrator import ActivatedSludgeCalibrator

class ASM2DCalibrator(ActivatedSludgeCalibrator):
    """Calibrateur spécifique pour ASM2d"""

    def get_convergence_parameters(self) -> List[str]:
        """
        Retourne la lsite des paramètres à vérifier pour la convergence

        Returns:
            List[str]: Noms des paramètres
        """
        return [
            'so2',
            'snh4',
            'sno3',
            'spo4',
            'sf',
            'sa',
            'xh',
            'xpao',
            'xaut',
            'xpha',
            'xpp'
        ]

    def get_key_output_parameters(self) -> List[str]:
        """
        Retourne les paramètres clés à extraire

        Returns:
            List[str]: Noms des paramètres de sortie
        """
        return [
            'so2',
            'sf',
            'sa',
            'si',
            'snh4',
            'sno3',
            'sn2',
            'spo4',
            'salk',
            'xi',
            'xs',
            'xh',
            'xpao',
            'xpp',
            'xpha',
            'xaut',
            'xtss',
            'xmeoh',
            'xmep'
        ]