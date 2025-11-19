from typing import Dict, Any, List

from .activated_sludge_calibrator import ActivatedSludgeCalibrator

class AnoxicDenitrificationCalibrator(ActivatedSludgeCalibrator):
    """
    Calibrateur spécialisé pour les systèmes avec dénitrification

    Ajoute des paramètres spécifiques pour les zones anoxiques
    """

    def __init__(
            self,
            config: Dict[str, Any],
            convergence_days: float = 250.0,
            tolerance: float = 0.01,
            check_interval: int = 50
    ) -> None:
        """
        Initialise le calibrateur pour dénitrification

        Args:
            config (Dict[str, Any]): Configuration
            convergence_days (float, optional): Durée plus longue (zone anoxique à équilibrer). Defaults to 250.0.
            tolerance (float, optional): Tolérance. Defaults to 0.01.
            check_interval (int, optional): Intervalle. Defaults to 50.
        """
        super().__init__(
            config=config,
            convergence_days=convergence_days,
            tolerance=tolerance,
            check_interval=check_interval
        )
        self.process_type = "activated_sludge_denitrification"

    def get_convergence_parameters(self) -> List[str]:
        """
        Ajoute les paramètres de dénitrification

        Returns:
            List[str]: Liste étendue de paramètres
        """
        base_params = super().get_convergence_parameters()

        additional = [
            'sno',
            'sn2'
        ]

        return base_params + additional