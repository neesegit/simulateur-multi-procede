"""
Classe de base abstraite pour tous les visualiseurs de modèles
"""
import plotly.graph_objects as go
import logging

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from pathlib import Path
from plotly.subplots import make_subplots
from datetime import datetime
from interfaces.visualisation.utils.layout_utils import hex_to_rgb, create_subplot_layout
from interfaces.visualisation.utils.io_utils import save

from .plot_config import PlotConfig

logger = logging.getLogger(__name__)

class BaseVisualizer(ABC):
    """Classe de base pour les visualiseurs de modèles"""

    TEMPLATE = 'plotly_white'
    DEFAULT_COLORS = [
        '#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd',
        '#8c564b', '#e377c2', '#7f7f7f', '#bcbd22', '#17becf'
    ]

    def __init__(self, model_type: str, model_definition: Any):
        """
        Args:
            model_type (str): Type du modèle (ASM1Model, ASM2dModel ...)
            model_definition (Any): Définition du modèle depuis le registre
        """
        self.model_type = model_type
        self.model_name = model_type.replace('Model', '').upper()
        self.model_definition = model_definition

        self.components_dict = model_definition.get_components_dict()
        self.metrics = model_definition.get_metrics_dict()

        logger.info(f"Visualiseur initialisé pour {self.model_name}")

    @abstractmethod
    def get_plot_configs(self) -> List[PlotConfig]:
        """
        Retourne la liste des configurations de plots pour ce modèle

        Returns:
            List[PlotConfig]: Liste des configurations de graphiques
        """
        pass

    def get_component_label(self, component: str) -> str:
        """Retourne le label lisible d'un composant"""
        return self.components_dict.get(component, component.lower())
    
    def extract_component_values(
            self,
            flows: List[Dict],
            component: str
    ) -> List[float]:
        """
        Extrait les valeurs temporelles d'un composant

        Args:
            flows (List[Dict]): Liste des flux temporels
            component (str): Nom du composant

        Returns:
            List[float]: Liste des valeurs
        """
        values = []
        for flow in flows:
            comp_dict = flow.get('components', {})
            values.append(comp_dict.get(component, 0.0))
        return values
    
    def extract_aggregate_values(
            self,
            flows: List[Dict],
            components: List[str]
    ) -> Dict[str, List[float]]:
        """
        Extrait les valeurs de plusieurs composants

        Args:
            flows (List[Dict]): Liste des flux temporels
            components (List[str]): Liste des noms de composants

        Returns:
            Dict[str, List[float]]: Dict {component: [values]}
        """
        result = {}
        for comp in components:
            result[comp] = self.extract_component_values(flows, comp)
        return result
    
    def get_metric_components(self, metric_key: str) -> List[str]:
        """
        Retourne les composants associés à une métrique

        Args:
            metric_key (str): Clé de la métrique (cod, tkn, biomass, etc)

        Returns:
            List[str]: Liste des composants
        """
        metric_value = self.metrics.get(metric_key, [])

        if isinstance(metric_value, list):
            return metric_value
        elif isinstance(metric_value, str):
            return [metric_value]
        else:
            return []
        
    def plot_stacked_area(
            self,
            fig: go.Figure,
            timestamps: List[datetime],
            components_data: Dict[str, List[float]],
            row: int,
            col: int,
            colors: Optional[List[str]] = None
    ) -> None:
        """
        Crée un graphique en aires empilées

        Args:
            fig (go.Figure): Figure Plotly 
            timestamps (List[datetime]): Liste des timestamps
            components_data (Dict[str, List[float]]): Dict {component: values}
            row (int), col (int): Position du subplot
            colors (Optional[List[str]], optional): Liste de couleurs. Defaults to None.
        """
        colors = colors or self.DEFAULT_COLORS
        cumulative = [0] * len(timestamps)

        for idx, (comp, values) in enumerate(components_data.items()):
            if not any(values):
                continue

            stacked_values = [c + v for c, v in zip(cumulative, values)]

            fig.add_trace(
                go.Scatter(
                    x=timestamps,
                    y=stacked_values,
                    mode='lines',
                    name=self.get_component_label(comp),
                    line=dict(width=0),
                    fillcolor=f'rgba({hex_to_rgb(colors[idx % len(colors)])}, 0.6)',
                    fill='tonexty' if idx > 0 else 'tozeroy',
                    legendgroup=f'stack_{row}_{col}',
                    showlegend=True
                ),
                row=row,
                col=col
            )

            cumulative = stacked_values

    def plot_lines(
            self,
            fig: go.Figure,
            timestamps: List[datetime],
            components_data: Dict[str, List[float]],
            row: int,
            col: int,
            colors: Optional[list[str]] = None,
            show_setpoint: bool = False,
            setpoint_value: Optional[float] = None
    ) -> None:
        """
        Crée un graphique en lignes

        Args:
            fig (go.Figure): Figure Plotly
            timestamps (List[datetime]): Liste des timestamps
            components_data (Dict[str, List[float]]): Dict {component: values}
            row (int), col (int): Position du subplot
            colors (Optional[list[str]], optional): Liste de couleurs. Defaults to None.
            show_setpoint (bool, optional): Affiche une ligne de consigne. Defaults to False.
            setpoint_value (Optional[float], optional): Valeur de la consigne. Defaults to None.
        """
        colors = colors or self.DEFAULT_COLORS
        
        for idx, (comp, values) in enumerate(components_data.items()):
            if not any(values):
                continue

            fig.add_trace(
                go.Scatter(
                    x=timestamps,
                    y=values,
                    mode='lines',
                    name=self.get_component_label(comp),
                    line=dict(color=colors[idx%len(colors)], width=2),
                    legendgroup=f'lines_{row}_{col}',
                    showlegend=True
                ),
                row=row,
                col=col
            )
        
        if show_setpoint and setpoint_value is not None:
            fig.add_trace(
                go.Scatter(
                    x=timestamps,
                    y=[setpoint_value]*len(timestamps),
                    mode='lines',
                    name='Consigne',
                    line=dict(color='red', width=1, dash='dash'),
                    legendgroup=f'lines_{row}_{col}',
                    showlegend=True
                ),
                row=row,
                col=col
            )
    
    def create_dashboard(
            self,
            flows: List[Dict],
            timestamps: List[datetime],
            output_dir: str,
            node_id: str,
            show: bool = False,
            format: str = 'both'
    ) -> Optional[Path]:
        """
        Crée le dashboard complet

        Args:
            flows (List[Dict]): Liste des flux temporels
            timestamps (List[datetime]): Liste des timestamps
            output_dir (str): Répertoire de sortie
            node_id (str): ID du noeud
            show (bool, optional): Afficher le graphique. Defaults to False.
            format (str, optional): Format de sortie (html, png, both). Defaults to 'both'.

        Returns:
            Optional[Path]: Path du fichier crée
        """
        plot_configs = self.get_plot_configs()

        rows, cols = create_subplot_layout(len(plot_configs))

        subplot_titles = [config.title for config in plot_configs]
        fig = make_subplots(
            rows=rows,
            cols=cols,
            subplot_titles=subplot_titles,
            vertical_spacing=0.12,
            horizontal_spacing=0.10
        )

        for idx, config in enumerate(plot_configs):
            row, col = divmod(idx, cols)
            row += 1
            col += 1

            self._plot_single(fig, flows, timestamps, config, row, col)
            fig.update_yaxes(title_text=config.ylabel, row=row, col=col)
            fig.update_xaxes(title_text='Temps', row=row, col=col)

        fig.update_layout(
            title_text=f"Simulation - {node_id} ({self.model_name})",
            title_font_size=20,
            showlegend=True,
            template=self.TEMPLATE,
            height=300*rows,
            width=500*cols
        )

        saved_path = save(Path(output_dir), node_id, fig, height=300*rows, width=500*rows, format=format)

        if show:
            fig.show()

        return saved_path
        

    def _plot_single(
            self,
            fig: go.Figure,
            flows: List[Dict],
            timestamps: List[datetime],
            config: PlotConfig,
            row: int,
            col: int
    ) -> None:
        """Génère un graphique unique selon sa configuration"""

        if config.components:
            components_data = self.extract_aggregate_values(flows, config.components)
        else:
            components = self.get_metric_components(config.plot_type)
            components_data = self.extract_aggregate_values(flows, components)

        if config.plot_type in ['cod', 'tkn', 'ss']:
            total_values = [sum(components_data[c][i] for c in components_data) for i in range(len(timestamps))]
            self.plot_lines(
                fig, timestamps,
                {'Total': total_values},
                row, col,
                colors=['#1f77b4']
            )
        elif config.plot_type in ['biomass', 'substrates']:
            self.plot_stacked_area(
                fig, timestamps, components_data, row, col, config.colors
            )
        else:
            self.plot_lines(
                fig, timestamps, components_data, row, col, config.colors, config.show_setpoint, config.setpoint_value
            )