from typing import Type
from .plots.cod_plotter import CODPlotter
from .plots.nitrogen_plotter import NitrogenPlotter
from .plots.oxygen_plotter import OxygenPlotter
from .plots.biomass_plotter import BiomassPlotter
from .plots.substrates_plotter import SubstratesPlotter
from .plots.phosphorus_plotter import PhosphorusPlotter

PLOTTERS = {
    'cod': CODPlotter,
    'nitrogen': NitrogenPlotter,
    'oxygen': OxygenPlotter,
    'biomass': BiomassPlotter,
    'substrates': SubstratesPlotter,
    'phosphorus': PhosphorusPlotter
}

def get_plotter(plot_type: str) -> Type:
    if plot_type not in PLOTTERS:
        raise ValueError(f"Type de graphique inconnu : {plot_type}")
    return PLOTTERS[plot_type]