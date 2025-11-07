from .base_plotter import BasePlotter
from ..component_mapper import ComponentMapper

class NitrogenPlotter(BasePlotter):

    def plot(self):
        components_data = ComponentMapper.extract_values(self.flows, 'nitrogen', self.model_type)

        colors = ['#d62728', '#2ca02c', '#9467bd', '#8c564b']
        for idx, (comp, values) in enumerate(components_data.items()):
            if any(values):
                self._add_trace(
                    x=self.timestamps,
                    y=values,
                    mode='lines',
                    name=ComponentMapper.get_label(comp),
                    line=dict(color=colors[idx % len(colors)], width=2),
                    legendgroup='nitrogen',
                    showlegend=True
                )