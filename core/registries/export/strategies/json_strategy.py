"""Stratégie d'export JSON"""
import json
from pathlib import Path
from typing import Dict, Any
from .base import ExportStrategy


class JSONExportStrategy(ExportStrategy):
    """Export au format JSON"""

    @property
    def format_name(self) -> str:
        return "json"

    @property
    def file_extension(self) -> str:
        return ".json"

    def export(self, results: Dict[str, Any], output_path: Path, **kwargs) -> Path:
        filepath = output_path / f"{kwargs.get('name', 'simulation')}_full.json"
        with open(filepath, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        return filepath

    def supports_node(self, node_type: str) -> bool:
        return True
