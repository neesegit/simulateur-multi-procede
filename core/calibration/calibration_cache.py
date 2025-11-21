import json
import logging

from pathlib import Path
from typing import Optional

from .calibration_result import CalibrationResult

logger = logging.getLogger(__name__)

class CalibrationCache:
    """Gère la lecture/écriture des fichiers de calibration en cache"""

    def __init__(self, cache_dir: str = 'output/calibration'):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"CalibrationCache initialisé : {self.cache_dir}")

    def get_cache_path(self, process_id: str, model_type: str) -> Path:
        """Génère le chemin du fichier cache"""
        filename = f"{process_id}_{model_type}_calibration.json"
        return self.cache_dir / filename
    
    def save(self, result: CalibrationResult) -> Path:
        """Sauvegarde une calibration en cache"""
        cache_path = self.get_cache_path(
            result.metadata.process_id,
            result.metadata.model_type
        )

        with open(cache_path, 'w', encoding='utf-8') as f:
            json.dump(result.to_dict(), f, indent=2, default=str)

        logger.info(f"Calibration sauvegardée : {cache_path}")
        return cache_path
    
    def load(self, process_id: str, model_type: str) -> Optional[CalibrationResult]:
        """Charge une calibration depuis le cache"""
        cache_path = self.get_cache_path(process_id, model_type)
        
        if not cache_path.exists():
            logger.debug(f"Pas de calibration en cache pour {process_id}/{model_type}")
            return None
        
        try:
            with open(cache_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            logger.info(f"Calibration chargée depuis le cache : {cache_path}")
            return CalibrationResult.from_dict(data)
        except Exception as e:
            logger.error(f"Erreur lors de la lecture du cache : {e}")
            return None
        
    def exists(self, process_id: str, model_type: str) -> bool:
        """Vérifie si une calibration existe en cache"""
        return self.get_cache_path(process_id, model_type).exists()