import logging 

from typing import List, Dict, Any

from ..base_calibrator import BaseCalibrator

logger = logging.getLogger(__name__)

class ActivatedSludgeCalibrator(BaseCalibrator):
    """
    Calibrateur pour procédés de boues activées

    Cible les paramètres spécifiques à l'ASM1, ASM2d, ASM3
    """
    def __init__(
            self,
            config: Dict[str, Any],
            convergence_days: float = 200.0,
            tolerance: float = 0.01,
            check_interval: int = 50
    ) -> None:
        """
        Initialise le calibrateur pour boues activées

        Args:
            config (Dict[str, Any]): Configuration de simulation
            convergence_days (float, optional): Durée maximale. Defaults to 200.0.
            tolerance (float, optional): Tolérance de convergence. Defaults to 0.01.
            check_interval (int, optional): Intervalle de vérification. Defaults to 50.
        """
        super().__init__(
            config=config,
            convergence_days=convergence_days,
            tolerance=tolerance,
            check_interval=check_interval,
            process_type="activated_sludge"
        )

    def get_convergence_parameters(self) -> List[str]:
        """
        Paramètres clés pour les boues activées

        Returns:
            List[str]: Liste des paramètres à vérifier
        """
        return [
            'cod',
            'cod_soluble',
            'ss',
            'nh4',
            'no3',
            'po4',
            'biomass_concentration'
        ]
    
    def get_key_output_parameters(self) -> List[str]:
        """
        Paramètres principaux à exporter

        Returns:
            List[str]: Liste de paramètres clés
        """
        return [
            'cod',
            'cod_soluble',
            'cod_removal_rate',
            'ss',
            'nh4',
            'no3',
            'po4',
            'biomass_concentration',
            'hrt_hours',
            'srt_days',
            'svi',
            'aeration_energy_kwh'
        ]