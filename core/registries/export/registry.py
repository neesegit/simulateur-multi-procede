"""Registre centralisé des stratégies d'export"""
import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional

from .strategies import (
    ExportStrategy,
    CSVExportStrategy,
    JSONExportStrategy,
    ExcelExportStrategy,
    ParquetExportStrategy,
)

logger = logging.getLogger(__name__)

_CONFIG_DIR = Path(__file__).parent / 'config'

_ALL_STRATEGIES: Dict[str, ExportStrategy] = {
    'csv': CSVExportStrategy(),
    'json': JSONExportStrategy(),
    'excel': ExcelExportStrategy(),
    'parquet': ParquetExportStrategy(),
}


class ExportRegistry:
    """Registre centralisé des stratégies d'export"""

    _instance = None

    def __init__(self):
        self._strategies: Dict[str, ExportStrategy] = {}
        self._default_export: set = set()
        self._register_defaults()

    @classmethod
    def get_instance(cls) -> 'ExportRegistry':
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def _register_defaults(self):
        """Charge les formats par défaut depuis default_formats.json"""
        config_path = _CONFIG_DIR / 'default_formats.json'
        default_formats = ['csv', 'json']  # fallback

        if config_path.exists():
            with open(config_path, encoding='utf-8') as f:
                config = json.load(f)
            default_formats = config.get('defaults', default_formats)
        else:
            logger.warning(f"default_formats.json introuvable : {config_path}")

        for fmt in default_formats:
            strategy = _ALL_STRATEGIES.get(fmt)
            if strategy is None:
                logger.warning(f"Format par défaut inconnu : '{fmt}'")
                continue
            self.register(strategy, default=True)

    def register(self, strategy: ExportStrategy, default: bool = False):
        """Enregistre une stratégie d'export"""
        key = strategy.format_name.lower()
        if key in self._strategies:
            raise ValueError(f"Export type '{key}' is already registered")
        self._strategies[key] = strategy
        if default:
            self._default_export.add(key)
        logger.debug(f"Stratégie d'export enregistrée : {strategy.format_name}")

    def get_strategy(self, format_name: str) -> ExportStrategy:
        """Récupère la stratégie pour un format d'export"""
        key = format_name.lower()
        if key not in self._strategies:
            raise ValueError(
                f"Export type '{key}' is not registered. "
                f"Available exports: {list(self._strategies.keys())}"
            )
        return self._strategies[key]

    def get_available_formats(self) -> list[str]:
        return list(self._strategies.keys())

    def is_registered(self, format_name: str) -> bool:
        return format_name.lower() in self._strategies

    def unregister(self, format_name: str) -> None:
        key = format_name.lower()
        if key in self._default_export:
            raise ValueError(f"Cannot unregister default format '{key}'")
        if key not in self._strategies:
            raise ValueError(f"Export type '{key}' is not registered")
        del self._strategies[key]
        logger.debug(f"Stratégie d'export supprimée : {key}")

    def export(
        self,
        format_name: str,
        results: Dict[str, Any],
        output_path: Path,
        **kwargs
    ) -> Path:
        """Exporte les résultats dans le format spécifié"""
        strategy = self.get_strategy(format_name)
        output_path.mkdir(parents=True, exist_ok=True)
        try:
            filepath = strategy.export(results, output_path, **kwargs)
            logger.info(f"Export {format_name} réussi : {filepath}")
            return filepath
        except Exception as e:
            logger.error(f"Erreur lors de l'export {format_name} : {e}")
            raise

    def export_all(
        self,
        results: Dict[str, Any],
        output_dir: Path,
        formats: Optional[list[str]] = None,
        **kwargs
    ) -> Dict[str, Path]:
        """Exporte dans plusieurs formats"""
        if formats is None:
            formats = self.get_available_formats()

        exported = {}
        for format_name in formats:
            try:
                filepath = self.export(format_name, results, output_dir, **kwargs)
                exported[format_name] = filepath
            except Exception as e:
                logger.warning(f"Impossible d'exporter en {format_name} : {e}")

        return exported
