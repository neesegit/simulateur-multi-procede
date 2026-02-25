import sys
import io
import logging
from pathlib import Path

# Configuration du logging
def setup_logging(log_level: str = "INFO") -> logging.Logger:
    """Configure le système de logging"""
    Path('output/logs').mkdir(parents=True, exist_ok=True)

    # Force UTF-8 sur la console Windows (évite UnicodeEncodeError avec cp1252)
    if isinstance(sys.stdout, io.TextIOWrapper):
        sys.stdout.reconfigure(encoding='utf-8')
    if isinstance(sys.stderr, io.TextIOWrapper):
        sys.stderr.reconfigure(encoding='utf-8')

    numeric_level = getattr(logging, log_level.upper(), logging.INFO)

    logging.basicConfig(
        level=numeric_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('output/logs/simulation.log', encoding='utf-8'),
            logging.StreamHandler()
        ]
    )

    return logging.getLogger(__name__)