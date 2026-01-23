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

class TakacsVisualizer(BaseVisualizer):
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

            value.append(float(value) if value is not None else 0.0)
        
        return values
    
    def create_dashboard(self, flows: List[Dict], timestamps: List[datetime], output_dir: str, node_id: str, show: bool = False, format: str = 'both') -> Path | None:
        """
        Crée le dashboard pour le settler avec visualisation des couches
        """
        plot_configs = self.get_plot_configs()

        rows = 3
        cols = 2

        subplot_titles = [
            config.title for config in plot_configs
        ] + ['Profil de concentration (dernière étape)', '']

        fig = make_subplots(
            rows=rows,
            cols=cols,
            subplot_titles=subplot_titles,
            vertical_spacing=0.15,
            horizontal_spacing=0.15,
            specs=[
                [{'type': 'xy'}, {'type': 'xy'}],
                [{'type:' 'xy'}, {'type': 'xy'}],
                [{'type': 'xy', 'colspan': 2}, None]
            ]
        )

        for idx, config in enumerate(plot_configs):
            row = (idx // cols) + 1
            col = (idx % cols) + 1

            self._plot_single(fig, flows, timestamps, config, row, col)
            fig.update_yaxes(title_text=config.ylabel, row=row, col=col)
            fig.update_xaxes(title_text='Temps', row=row, col=col)

        self._plot_concentration_profile(fig, flows, 3, 1)

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
    
    def _plot_concentration_profile(
            self,
            fig: go.Figure,
            flows: List[Dict],
            row: int,
            col: int
    ) -> None:
        """
        Trace le profil de concentration dans les couches du settler
        """

        if not flows:
            return
        
        last_flow = flows[-1]
        layer_concentrations = last_flow.get('layer_concentrations', [])

        if not layer_concentrations:
            return
        
        n_layers = len(layer_concentrations)
        layers = list(range(n_layers))

        fig.add_trace(
            go.Scatter(
                x=layer_concentrations,
                y=layers,
                mode='lines+markers',
                name='Concentration TSS',
                line=dict(color='#1f77b4', width=3),
                marker=dict(size=8),
            ),
            row=row,
            col=col
        )

        feed_layer = last_flow.get('feed_layer', n_layers // 2)
        fig.add_hline(
            y=feed_layer,
            line_dash="dash",
            line_color="red",
            annotation_text="Alimentation",
            row=str(row),
            col=str(col)
        )

        sludge_blanket = last_flow.get('sludge_blanket', {})
        if sludge_blanket.get('has_blanket'):
            blanket_top = sludge_blanket.get('blanket_top_layer', 0)
            blanket_bottom = sludge_blanket.get('blanket_bottom_layer', 0)

            fig.add_hrect(
                y0=blanket_top,
                y1=blanket_bottom,
                fillcolor="orange",
                opacity=0.2,
                annotation_text="Voile de boues",
                row=str(row),
                col=str(col)
            )

        fig.update_xaxes(
            title_text='Concentration TSS (mg/L)',
            row=row,
            col=col
        )
        fig.update_yaxes(
            title_text='Couche (0=surface, N=fond)',
            row=row,
            col=col,
            autorange="reversed"
        )
