"""
Visualiseur pour le modèle Linear Regression
"""
from typing import List
from ..base.plot_config import PlotConfig
from .ml_base_visualizer import MLBaseVisualizer


class LINEARVisualizer(MLBaseVisualizer):
    """Visualiseur pour le modèle Linear Regression"""

    def get_plot_configs(self) -> List[PlotConfig]:
        return [
            PlotConfig(
                title='DCO',
                ylabel='DCO (mg/L)',
                plot_type='cod',
                components=['cod'],
                colors=['#1f77b4']
            ),
            PlotConfig(
                title='Azote (NH4 / NO3)',
                ylabel='Azote (mg N/L)',
                plot_type='nitrogen',
                components=['nh4', 'no3'],
                colors=['#d62728', '#2ca02c']
            ),
            PlotConfig(
                title='MES',
                ylabel='MES (mg/L)',
                plot_type='tss',
                components=['tss'],
                colors=['#8c564b']
            ),
            PlotConfig(
                title="Taux d'épuration DCO",
                ylabel='Élimination DCO (%)',
                plot_type='removal',
                components=['cod_removal'],
                colors=['#17becf']
            ),
        ]
