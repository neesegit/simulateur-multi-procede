"""
Visualiseur de base pour les modèles ML (LinearModel, RandomForestModel).

Affiche un dashboard de type snapshot plutôt qu'une série temporelle,
car un modèle statique produit des valeurs identiques à chaque pas
si l'influent est constant.
"""
import logging

from typing import List, Dict, Optional
from pathlib import Path
from datetime import datetime

import plotly.graph_objects as go
from plotly.subplots import make_subplots

from interfaces.visualisation.base.base_visualizer import BaseVisualizer
from interfaces.visualisation.utils.io_utils import save

logger = logging.getLogger(__name__)


class MLBaseVisualizer(BaseVisualizer):
    """
    Visualiseur dédié aux modèles ML.

    Dashboard en 4 panneaux :
    - Influent vs Effluent (bar groupé)
    - Taux d'épuration % (bar horizontal)
    - Paramètres opérationnels HRT / SRT (bar)
    - Évolution temporelle du taux d'épuration DCO (série temporelle)
    """

    @staticmethod
    def _get(flow: Dict, key: str, default: float = 0.0) -> float:
        """Lit une valeur depuis un flow sérialisé (top-level ou dans components)."""
        if key in flow:
            return float(flow[key])
        return float(flow.get('components', {}).get(key, default))

    def create_dashboard(
        self,
        flows: List[Dict],
        timestamps: List[datetime],
        output_dir: str,
        node_id: str,
        show: bool = False,
        format: str = 'both'
    ) -> Optional[Path]:

        last = flows[-1]

        # --- Effluent (clés standard FlowData → top-level dans le dict sérialisé) ---
        cod_out = self._get(last, 'cod')
        nh4_out = self._get(last, 'nh4')
        no3_out = self._get(last, 'no3')
        tss_out = self._get(last, 'tss')

        # --- Influent (clés non-standard → stockées dans components) ---
        cod_in = self._get(last, 'cod_in')
        tss_in = self._get(last, 'tss_in')
        nh4_in = self._get(last, 'nh4_in')
        no3_in = self._get(last, 'no3_in')

        # --- KPIs (clés non-standard → dans components) ---
        hrt_hours   = self._get(last, 'hrt_hours')
        srt_days    = self._get(last, 'srt_days')
        cod_removal = self._get(last, 'cod_removal_rate')

        nh4_removal = (
            max(0.0, (nh4_in - nh4_out) / nh4_in * 100.0) if nh4_in > 0 else 0.0
        )
        tss_removal = (
            max(0.0, (tss_in - tss_out) / tss_in * 100.0) if tss_in > 0 else 0.0
        )

        cod_removal_timeline = [self._get(f, 'cod_removal_rate') for f in flows]

        fig = make_subplots(
            rows=2, cols=2,
            subplot_titles=[
                'Influent vs Effluent (mg/L)',
                "Taux d'épuration (%)",
                'Paramètres opérationnels',
                "Évolution — Taux d'épuration DCO",
            ],
            vertical_spacing=0.22,
            horizontal_spacing=0.15,
        )

        # --- [1,1] Influent vs Effluent grouped bar ---
        labels       = ['DCO', 'NH₄', 'NO₃', 'MES']
        influent_vals = [cod_in,  nh4_in,  no3_in,  tss_in]
        effluent_vals = [cod_out, nh4_out, no3_out, tss_out]

        fig.add_trace(go.Bar(
            name='Influent',
            x=labels, y=influent_vals,
            marker_color='#aec7e8',
            legendgroup='compare',
        ), row=1, col=1)

        fig.add_trace(go.Bar(
            name='Effluent',
            x=labels, y=effluent_vals,
            marker_color='#1f77b4',
            legendgroup='compare',
        ), row=1, col=1)

        # --- [1,2] Removal rates horizontal bar ---
        removal_labels = ['DCO', 'NH₄', 'MES']
        removal_vals   = [cod_removal, nh4_removal, tss_removal]

        fig.add_trace(go.Bar(
            name="Taux d'épuration",
            x=removal_vals,
            y=removal_labels,
            orientation='h',
            marker_color=['#2ca02c', '#d62728', '#8c564b'],
            text=[f"{v:.1f} %" for v in removal_vals],
            textposition='outside',
            showlegend=False,
        ), row=1, col=2)

        # --- [2,1] HRT / SRT bar ---
        fig.add_trace(go.Bar(
            name='Paramètres',
            x=['HRT (h)', 'SRT (j)'],
            y=[hrt_hours, srt_days],
            marker_color=['#ff7f0e', '#9467bd'],
            text=[f"{hrt_hours:.1f} h", f"{srt_days:.1f} j"],
            textposition='outside',
            showlegend=False,
        ), row=2, col=1)

        # --- [2,2] COD removal time series ---
        fig.add_trace(go.Scatter(
            x=timestamps,
            y=cod_removal_timeline,
            mode='lines',
            name='Épuration DCO (%)',
            line=dict(color='#17becf', width=2),
            showlegend=False,
        ), row=2, col=2)

        fig.update_yaxes(title_text='Concentration (mg/L)', row=1, col=1)
        fig.update_xaxes(title_text='Élimination (%)', range=[0, 110], row=1, col=2)
        fig.update_yaxes(title_text='Valeur', row=2, col=1)
        fig.update_yaxes(title_text='Épuration DCO (%)', row=2, col=2)
        fig.update_xaxes(title_text='Temps', row=2, col=2)

        fig.update_layout(
            barmode='group',
            title_text=f"Simulation ML — {node_id} ({self.model_name})",
            title_font_size=20,
            showlegend=True,
            template=self.TEMPLATE,
            height=620,
            width=1100,
        )

        saved_path = save(Path(output_dir), node_id, fig, height=620, width=1100, format=format)

        if show:
            fig.show()

        return saved_path
