import logging

from typing import Dict, Any, List, Optional

from .base_calibrator import BaseCalibrator
from .calibration_result import CalibrationResult
from .biological.asm1_calibrator import ASM1Calibrator
from .biological.asm2d_calibrator import ASM2DCalibrator
from .biological.asm3_calibrator import ASM3Calibrator

class CalibrationManager:
    """
    Orchestre le processus de calibration pour une simulation complète
    """

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.calibrators: Dict[str, BaseCalibrator] = {}

    def create_calibrators(self) -> List[BaseCalibrator]:
        """Crée les calibraterus nécessaires pour la configuration"""
        self.calibrators.clear()
        calibrators = []

        processes_config = self.config.get('processes', [])

        for proc_config in processes_config:
            process_id = proc_config.get('node_id')
            model_type = proc_config.get('config', {}).get('model', 'ASM1')

            if not model_type.lower().endswith("model"):
                model_type += "Model"
            
            calibrator_class = self._get_calibrator_class(model_type)
            calibrator = calibrator_class(
                process_id=process_id,
                process_config=proc_config,
                model_type=model_type
            )

            self.calibrators[process_id] = calibrator
            calibrators.append(calibrator)
        return calibrators

    def _get_calibrator_class(self, model_type: str) -> type:
        """Retourne la classe de calibrateur appropriée"""
        mapping = {
            'ASM1Model': ASM1Calibrator,
            'ASM2dModel': ASM2DCalibrator,
            'ASM3Model': ASM3Calibrator
        }

        calibrator = mapping.get(model_type)
        if calibrator is None:
            self.logger.warning(
                f"Modèle {model_type} non reconnu, utilisation ASM1Calibrator"
            )
            return ASM1Calibrator
        
        return calibrator
    
    def run_all(
            self,
            skip_if_exists: bool = False,
            interactive: bool = False
    ) -> Dict[str, Optional[CalibrationResult]]:
        """
        Lance la calibration pour tous les procédés

        Args:
            skip_if_exists (bool, optional): Utilise les calibrations existantes si valides. Defaults to False.
            interactive (bool, optional): Demande confirmation avant chaque calibration. Defaults to False.

        Returns:
            Dict[str, Optional[CalibrationResult]]
        """
        calibrators = self.create_calibrators()
        results = {}

        print("\n"+"="*70)
        print(f"Gestion de calibration - {len(calibrators)} procédé(s)")
        print("="*70)

        for calibrator in calibrators:
            result = calibrator.run(
                skip_if_exists=skip_if_exists,
                interactive=interactive
            )
            results[calibrator.process_id] = result
        return results
    
    def get_steady_states(
            self,
            process_id: str
    ) -> Optional[Dict[str, float]]:
        """Récupère les steady-states pour un procédé"""
        if process_id not in self.calibrators:
            self.logger.warning(f"Procédé {process_id} non trouvé")
            return None
        
        calibrator = self.calibrators[process_id]
        cached = calibrator.cache.load(process_id, calibrator.model_type)

        if cached is None:
            return None
        
        steady_states = cached.steady_states
        if steady_states:
            return list(steady_states.values())[0]
        return None