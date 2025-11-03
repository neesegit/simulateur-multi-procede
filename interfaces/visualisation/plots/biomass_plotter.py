from ..base_plotter import BasePlotter
from ..component_mapper import ComponentMapper

class BiomassPlotter(BasePlotter):

    def plot(self):
        biomass_het = ComponentMapper.extract_values(self.flows, 'biomass_heterotrophs', self.model_type)
        biomass_aut = ComponentMapper.extract_values(self.flows, 'biomass_autotrophs', self.model_type)
        biomass_pao = ComponentMapper.extract_values(self.flows, 'biomass_pao', self.model_type)

        het_values = [0]*len(self.timestamps)
        aut_values = [0]*len(self.timestamps)

        for comp, values in biomass_het.items():
            if any(values):
                self._add_trace(
                    x=self.timestamps,
                    y=values,
                    mode='lines',
                    name=ComponentMapper.get_label(comp),
                    line=dict(width=0),
                    fillcolor='rgba(140, 86, 75, 0.6)',
                    fill='tozeroy',
                    legendgroup='biomass',
                    showlegend=True
                )
                het_values = values
        for comp, values in biomass_aut.items():
            if any(values):
                stacked_values = [h + a for h, a in zip(het_values, values)]
                self._add_trace(
                    x=self.timestamps,
                    y=stacked_values,
                    mode='lines',
                    name=ComponentMapper.get_label(comp),
                    line=dict(width=0),
                    fillcolor='rgba(227, 119, 194, 0.6)',
                    fill='tonexty',
                    legendgroup='biomass',
                    showlegend=True
                )
                aut_values = stacked_values
        for comp, values in biomass_pao.items():
            if any(values):
                stacked_values = [a + p for a, p in zip(aut_values, values)]
                self._add_trace(
                    x=self.timestamps,
                    y=stacked_values,
                    mode='lines',
                    name=ComponentMapper.get_label(comp),
                    line=dict(width=0),
                    fillcolor='rgba(148, 103, 189, 0.6)',
                    fill='tonexty',
                    legendgroup='biomass',
                    showlegend=True
                )