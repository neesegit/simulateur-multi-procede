from pathlib import Path
import logging

logger: logging.Logger = logging.getLogger(__name__)

def setup_directories() -> None:
    """Crée la structure de répertoires nécessaire"""
    directories: list[str] = [
        'output/results',
        'output/logs',
        'output/figures',
        'config',
        'data/raw',
        'data/processed'
    ]
    for dir_path in directories:
        Path(dir_path).mkdir(parents=True, exist_ok=True)
    
    logger.debug("Structure de répertoires initialisée")