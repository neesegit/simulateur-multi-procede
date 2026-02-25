"""Stratégie d'export Excel"""
from pathlib import Path
from typing import Dict, Any
from .base import ExportStrategy


class ExcelExportStrategy(ExportStrategy):
    """Export au format Excel avec plusieurs feuilles"""

    @property
    def format_name(self) -> str:
        return "excel"

    @property
    def file_extension(self) -> str:
        return ".xlsx"

    def export(self, results: Dict[str, Any], output_path: Path, **kwargs) -> Path:
        import pandas as pd

        filepath = output_path / f"{kwargs.get('name', 'simulation')}_results.xlsx"

        with pd.ExcelWriter(filepath, engine='openpyxl') as writer:
            metadata = results.get('metadata', {})
            pd.DataFrame([metadata]).to_excel(writer, sheet_name='Metadata', index=False)

            history = results.get('history', {})
            for node_id, flows in history.items():
                if not flows:
                    continue
                data = []
                for flow in flows:
                    row = {
                        'timestamp': flow.get('timestamp'),
                        'flowrate': flow.get('flowrate'),
                        **flow.get('components', {})
                    }
                    data.append(row)
                df = pd.DataFrame(data)
                df.to_excel(writer, sheet_name=node_id[:31], index=False)

        return filepath

    def supports_node(self, node_type: str) -> bool:
        return True
