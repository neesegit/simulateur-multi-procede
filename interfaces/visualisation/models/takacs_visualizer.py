"""
Visualiseur spécifique pour le modèle Takacs
"""
from pathlib import Path
import numpy as np
import plotly.graph_objects as go

from typing import List, Dict, Optional
from datetime import datetime
from ..base.base_visualizer import BaseVisualizer
from ..base.plot_config import PlotConfig
from plotly.subplots import make_subplots
from pathlib import Path
from ..utils.io_utils import save

class TAKACSVisualizer(BaseVisualizer):
    """Visualiseur pour le modèle de décantation Takacs"""

    def get_plot_configs(self) -> List[PlotConfig]:
        """Configure les graphiques spécifiques au settler"""

        configs = [
            PlotConfig(
                title='Efficacité de séparation',
                ylabel='Efficacité (%)',
                plot_type='efficiency',
                components=['removal_efficiency'],
                colors=['#1f77b4']
            ),
            PlotConfig(
                title='Qualité de l\'effluent (overflow)',
                ylabel='TSS (mg/L)',
                plot_type='overflow_quality',
                components=['X_overflow'],
                colors=['#2ca02c']
            ),
            PlotConfig(
                title='Concentration soutirage (underflow)',
                ylabel='TSS (mg/L)',
                plot_type='undeflow_quality',
                components=['X_underflow'],
                colors=['#d62728']
            ),
            PlotConfig(
                title='Charges hydraulique et massique',
                ylabel='Charge',
                plot_type='loading',
                components=['surface_loading', 'solids_loading'],
                colors=['#ff7f0e', '#9467bd']
            ),
        ]

        return configs
    
    def extract_component_values(self, flows: List[Dict], component: str) -> List[float]:
        """
        Extrait les valeurs temporelles d'un composant depuis les flows
        """
        values = []
        for flow in flows:
            value = flow.get(component)

            if value is None:
                comp_dict = flow.get('components', {})
                value = comp_dict.get(component, 0.0)

            values.append(float(value) if value is not None else 0.0)
        
        return values
    
    def create_dashboard(self, flows: List[Dict], timestamps: List[datetime], output_dir: str, node_id: str, show: bool = False, format: str = 'both') -> Path | None:
        """
        Crée le dashboard pour le settler avec visualisation des couches
        """
        plot_configs = self.get_plot_configs()

        rows = 2
        cols = 2

        subplot_titles = [
            config.title for config in plot_configs
        ]

        fig = make_subplots(
            rows=rows,
            cols=cols,
            subplot_titles=subplot_titles,
            vertical_spacing=0.15,
            horizontal_spacing=0.15,
            specs=[
                [{'type': 'xy'}, {'type': 'xy'}],
                [{'type': 'xy'}, {'type': 'xy'}],
                [{'type': 'xy', 'colspan': 2}, None]
            ]
        )

        for idx, config in enumerate(plot_configs):
            row = (idx // cols) + 1
            col = (idx % cols) + 1

            self._plot_single(fig, flows, timestamps, config, row, col)
            fig.update_yaxes(title_text=config.ylabel, row=row, col=col)
            fig.update_xaxes(title_text='Temps', row=row, col=col)


        fig.update_layout(
            title_text=f"Décanteur Secondaire - {node_id}",
            title_font_size=20,
            showlegend=True,
            template=self.TEMPLATE,
            height=900,
            width=1200
        )

        saved_path = save(
            Path(output_dir),
            node_id,
            fig,
            height=900,
            width=1200,
            format=format
        )

        if show:
            fig.show()

        return saved_path