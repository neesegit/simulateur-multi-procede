"""
Visualiseur spécifique pour le modèle ASM1
"""
from typing import List
from ..base.base_visualizer import BaseVisualizer
from ..base.plot_config import PlotConfig

class ASM1Visualizer(BaseVisualizer):
    """Visualiseur pour le modèle ASM1"""

    def get_plot_configs(self) -> List[PlotConfig]:
        """Configure les graphiques spécifiques à ASM1"""

        configs = [
            PlotConfig(
                title='DCO',
                ylabel='DCO (g/L)',
                plot_type='cod',
                components=self.get_metric_components('cod'),
                colors=['#1f77b4', '#ff7f0e', '#2ca02c']
            ),
            PlotConfig(
                title='Composés Azotés',
                ylabel='Azote (g N/L)',
                plot_type='nitrogen',
                components=self.get_metric_components('tkn'),
                colors=['#d62728', '#2ca02c', '#9467bd', '#8c564b']
            ),
            PlotConfig(
                title='Biomasse Active',
                ylabel='Biomasse (g COD/L)',
                plot_type='biomass',
                components=self.get_metric_components('biomass'),
                colors=['#8c564b', '#e377c2']
            ),
            PlotConfig(
                title='Substrats Organiques',
                ylabel='Substrat (g COD/L)',
                plot_type='substrates',
                components=['ss', 'xs'],
                colors=['#9467bd', '#8c564b']
            ),
        ]

        return configs