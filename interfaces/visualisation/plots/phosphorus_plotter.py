from .base_plotter import BasePlotter
from ..component_mapper import ComponentMapper

class PhosphorusPlotter(BasePlotter):

    def plot(self):
        phosphorus_data = ComponentMapper.extract_values(self.flows, 'phosphorus', self.model_type)

        colors = ['#17becf', '#bcbd22']

        for idx, (comp, values) in enumerate(phosphorus_data.items()):
            if any(values):
                self._add_trace(
                    x=self.timestamps,
                    y=values,
                    mode='lines',
                    name=ComponentMapper.get_label(comp),
                    line=dict(color=colors[idx % len(colors)], width=2),
                    legendgroup='phosphorus',
                    showlegend=True
                )