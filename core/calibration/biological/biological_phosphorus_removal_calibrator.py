from typing import Dict, Any, List

from .activated_sludge_calibrator import ActivatedSludgeCalibrator

class BiologicalPhosphorusRemovalCalibrator(ActivatedSludgeCalibrator):
    """
    Calibrateur pour systèmes avec élimination biologique du phosphore

    Spécifique à ASM2d avec PAO
    """

    def __init__(
            self,
            config: Dict[str, Any],
            convergence_days: float = 300.0,
            tolerance: float = 0.01,
            check_interval: int = 50
    ) -> None:
        """
        Initialise le calibrateur pour BPR

        Args:
            config (Dict[str, Any]): Configuration
            convergence_days (float, optional): Durée plus longue (cycles aérobic/anoxic). Defaults to 300.0.
            tolerance (float, optional): Tolérance. Defaults to 0.01.
            check_interval (int, optional): Intervalle. Defaults to 50.
        """
        super().__init__(
            config=config,
            convergence_days=convergence_days,
            tolerance=tolerance,
            check_interval=check_interval
        )
        self.process_type = "activated_sludge_bpr"

    def get_convergence_parameters(self) -> List[str]:
        """
        Paramètres incluant le stockage de phosphore

        Returns:
            List[str]: Liste des paramètre BPR
        """
        base_params = super().get_convergence_parameters()

        additional = [
            'spo4',
            'xpao',
            'xpp'
        ]

        return base_params + additional
    
    def get_key_output_parameters(self) -> List[str]:
        """
        Paramètres de sortie incluent P

        Returns:
            List[str]: Liste de paramètres
        """
        base_params = super().get_key_output_parameters()
        
        additional = [
            'xpao',
            'xpp',
            'xpha'
        ]

        return base_params + additional