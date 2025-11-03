from ..base_plotter import BasePlotter
from ..component_mapper import ComponentMapper

class SubstratesPlotter(BasePlotter):

    def plot(self):
        substrates_data = ComponentMapper.extract_values(self.flows, 'substrates', self.model_type)

        colors = ['#9467bd', '#8c564b', '#e377c2']

        for idx, (comp, values) in enumerate(substrates_data.items()):
            if any(values):
                self._add_trace(
                    x=self.timestamps,
                    y=values,
                    mode='lines',
                    name=ComponentMapper.get_label(comp),
                    line=dict(color=colors[idx % len(colors)], width=2),
                    legendgroup='substrates',
                    showlegend=True
                )