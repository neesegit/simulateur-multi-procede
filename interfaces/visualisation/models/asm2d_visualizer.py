"""
Visualiseur spécifique pour le modèle ASM2d
"""
from typing import List
from ..base.base_visualizer import BaseVisualizer
from ..base.plot_config import PlotConfig

class ASM2DVisualizer(BaseVisualizer):
    """Visualiseur pour le modèle ASM2d"""

    def get_plot_configs(self) -> List[PlotConfig]:
        """Configure les graphiques spécifiques à ASM2d"""

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
                components=['snh4', 'sno3', 'sn2'],
                colors=['#d62728', '#2ca02c', '#9467bd']
            ),
            PlotConfig(
                title='Biomasse Active',
                ylabel='Biomasse (g COD/L)',
                plot_type='biomass',
                components=self.get_metric_components('biomass'),
                colors=['#8c564b', '#e377c2', '#9467bd']
            ),
            PlotConfig(
                title='Substrats Organiques',
                ylabel='Substrat (g COD/L)',
                plot_type='substrates',
                components=['sf', 'sa', 'xs'],
                colors=['#9467bd', '#8c564b', '#e377c2']
            ),
            PlotConfig(
                title='Phosphore',
                ylabel='Phosphore (g P/L)',
                plot_type='phosphorus',
                components=['spo4', 'xpp'],
                colors=['#17becf', '#bcbd22']
            ),
        ]

        return configs