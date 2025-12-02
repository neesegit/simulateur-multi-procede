import logging
import json

from pathlib import Path
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)

class MLTrainingCache:
    """Gère le cache des modèles ML entraînés"""

    def __init__(self, cache_dir: str = 'output/ml_training'):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"MLTrainingCache initialisé : {self.cache_dir}")

    def get_cache_path(self, process_id: str, model_type: str, config_hash: str) -> Path:
        """Génère le chemin du modèle entraîné"""
        short_hash = config_hash[:8]

        if model_type == 'RNNModel':
            model_file = f"{process_id}_{model_type}_{short_hash}.keras"
        else:
            model_file = f"{process_id}_{model_type}_{short_hash}.pkl"

        return self.cache_dir / model_file
    
    def get_metadata_path(self, process_id: str, model_type: str, config_hash: str) -> Path:
        """Génère le chemin du fichier de métadonnées"""
        short_hash = config_hash[:8]
        return self.cache_dir / f"{process_id}_{model_type}_{short_hash}_meta.json"
    
    def exists(self, process_id: str, model_type: str, config_hash: str) -> bool:
        """Vérifie si un modèle entraîné existe"""
        model_path = self.get_cache_path(process_id, model_type, config_hash)
        meta_path = self.get_metadata_path(process_id, model_type, config_hash)
        return model_path.exists() and meta_path.exists()
    
    def save_metadata(
            self,
            process_id: str,
            model_type: str,
            config_hash: str,
            metadata: Dict[str, Any]
    ) -> None:
        """Sauvegarde les métadonnées d'entraînement"""
        meta_path = self.get_metadata_path(process_id, model_type, config_hash)

        with open(meta_path, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, indent=2, default=str)
        
        logger.info(f"Métadonnées sauvegardées : {meta_path}")

    def load_metadata(
            self,
            process_id: str,
            model_type: str,
            config_hash: str
    ) -> Optional[Dict[str, Any]]:
        """Charge les métadonnées d'entraînement"""
        meta_path = self.get_metadata_path(process_id, model_type, config_hash)

        if not meta_path.exists():
            return None
        
        try:
            with open(meta_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Erreur lors de la lecture des métadonnées : {e}")
            return None