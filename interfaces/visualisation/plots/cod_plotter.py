from .base_plotter import BasePlotter

class CODPlotter(BasePlotter):

    def plot(self):
        cod_values = [f.get('cod',0) for f in self.flows]
        cod_soluble = [f.get('cod_soluble', 0) for f in self.flows]
        cod_particulate = [f.get('cod_particulate', 0) for f in self.flows]

        if any(cod_values):
            self._add_trace(
                x=self.timestamps, y=cod_values, mode='lines',
                name='DCO totale', line=dict(color='#1f77b4', width=2),
                legendgroup='cod', showlegend=True
            )

        if any(cod_soluble):
            self._add_trace(
                x=self.timestamps,
                y=cod_soluble,
                mode='lines',
                name='DCO soluble',
                line=dict(color='#ff7f0e', width=2, dash='dash'),
                legendgroup='cod',
                showlegend=True
            )

        if any(cod_particulate):
            self._add_trace(
                x=self.timestamps,
                y=cod_particulate,
                mode='lines',
                name='DCO particulaire',
                line=dict(color='#2ca02c', width=2, dash='dot'),
                legendgroup='cod',
                showlegend=True
            )