import logging
from pathlib import Path

# Configuration du logging
def setup_logging(log_level: str = "INFO") -> logging.Logger:
    """Configure le système de logging"""
    Path('output/logs').mkdir(parents=True, exist_ok=True)

    numeric_level = getattr(logging, log_level.upper(), logging.INFO)

    logging.basicConfig(
        level=numeric_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('output/logs/simulation.log'),
            logging.StreamHandler()
        ]
    )

    return logging.getLogger(__name__)