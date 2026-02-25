"""Stratégie d'export CSV"""
from pathlib import Path
from typing import Dict, Any
from .base import ExportStrategy


class CSVExportStrategy(ExportStrategy):
    """Export au format CSV"""

    @property
    def format_name(self) -> str:
        return "csv"

    @property
    def file_extension(self) -> str:
        return ".csv"

    def export(self, results: Dict[str, Any], output_path: Path, **kwargs) -> Path:
        import pandas as pd

        history = results.get('history', {})
        node_id = kwargs.get('node_id')

        if node_id and node_id in history:
            flows = history[node_id]
            data = []
            for flow in flows:
                row = {
                    'timestamp': flow.get('timestamp'),
                    'flowrate': flow.get('flowrate'),
                    'temperature': flow.get('temperature'),
                    **flow.get('components', {})
                }
                data.append(row)

            df = pd.DataFrame(data)
            filepath = output_path / f"{node_id}_results.csv"
            df.to_csv(filepath, index=False)
            return filepath

        raise ValueError(f"Node {node_id} not found in results")

    def supports_node(self, node_type: str) -> bool:
        return True
