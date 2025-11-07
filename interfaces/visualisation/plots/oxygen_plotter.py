from .base_plotter import BasePlotter
from ..component_mapper import ComponentMapper

class OxygenPlotter(BasePlotter):

    def plot(self):
        oxygen_comps = ComponentMapper.get_components('oxygen', self.model_type)

        if oxygen_comps:
            comp = oxygen_comps[0]
            values = [f.get('components', {}).get(comp, 0) for f in self.flows]

            if any(values):
                self._add_trace(
                    x=self.timestamps,
                    y=values,
                    mode='lines',
                    name='O2 mesuré',
                    line=dict(color='#ff7f0e', width=2),
                    legendgroup='oxygen',
                    showlegend=True
                )
            self._add_trace(
                x=self.timestamps,
                y=[2.0] * len(self.timestamps),
                mode='lines',
                name='Consigne',
                line=dict(color='red', width=1, dash='dash'),
                legendgroup='oxygen',
                showlegend=True
            )