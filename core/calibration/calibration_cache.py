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

    def get_cache_path(self, process_id: str, model_type: str, config_hash: Optional[str] = None) -> Path:
        """
        Génère le chamin du fichier cache

        Args:
            process_id (str): ID du procédé
            model_type (str): Type de modèle
            config_hash (Optional[str], optional): Hash de la configuration. Defaults to None.

        Returns:
            Path: Chemin du fichier cache
        """
        if config_hash:
            short_hash = config_hash[:8]
            filename = f"{process_id}_{model_type}_{short_hash}.json"
        else:
            filename = f"{process_id}_{model_type}_calibration.json"
        return self.cache_dir / filename
    
    def save(self, result: CalibrationResult) -> Path:
        """Sauvegarde une calibration en cache"""
        cache_path = self.get_cache_path(
            result.metadata.process_id,
            result.metadata.model_type,
            result.metadata.config_hash
        )

        with open(cache_path, 'w', encoding='utf-8') as f:
            json.dump(result.to_dict(), f, indent=2, default=str)

        logger.info(f"Calibration sauvegardée : {cache_path}")
        return cache_path
    
    def load(self, process_id: str, model_type: str, config_hash: Optional[str] = None) -> Optional[CalibrationResult]:
        """Charge une calibration depuis le cache"""
        cache_path = self.get_cache_path(process_id, model_type, config_hash)
        
        if not cache_path.exists():
            old_path = self.get_cache_path(process_id, model_type, None)
            if old_path.exists():
                logger.info(f"Utilisation du cache ancien format : {old_path.name}")
                cache_path = old_path
            else:
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
        
    def exists(self, process_id: str, model_type: str, config_hash: Optional[str] = None) -> bool:
        """Vérifie si une calibration existe en cache"""
        cache_path = self.get_cache_path(process_id, model_type, config_hash)
        if cache_path.exists():
            return True
        
        old_path = self.get_cache_path(process_id, model_type, None)
        return old_path.exists()