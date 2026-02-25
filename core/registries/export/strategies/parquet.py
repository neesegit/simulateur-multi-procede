"""Stratégie d'export Parquet"""
from pathlib import Path
from typing import Dict, Any
from .base import ExportStrategy


class ParquetExportStrategy(ExportStrategy):
    """Export au format Parquet (efficace pour big data)"""

    @property
    def format_name(self) -> str:
        return "parquet"

    @property
    def file_extension(self) -> str:
        return ".parquet"

    def export(self, results: Dict[str, Any], output_path: Path, **kwargs) -> Path:
        import pandas as pd

        node_id = kwargs.get('node_id')
        history = results.get('history', {})

        if node_id not in history:
            raise ValueError(f"Node {node_id} not found")

        flows = history[node_id]
        data = []
        for flow in flows:
            row = {
                'timestamp': flow.get('timestamp'),
                'flowrate': flow.get('flowrate'),
                **flow.get('components', {})
            }
            data.append(row)

        df = pd.DataFrame(data)
        filepath = output_path / f"{node_id}_results.parquet"
        df.to_parquet(filepath, index=False, compression='snappy')
        return filepath

    def supports_node(self, node_type: str) -> bool:
        return True
