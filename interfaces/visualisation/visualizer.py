"""
Module de visualisation des résultats de simulation

Rôle :
- Générer des graphiques de simulation
- Créer des dashboards comparatifs
- Sauvegarder les figures
"""
import logging 

import plotly.graph_objects as go
from plotly.subplots import make_subplots

from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional

from .component_mapper import ComponentMapper
from .plot_factory import get_plotter
from .utils.layout_utils import create_subplot_layout
from .utils.timestamp_utils import extract_timestamps
from .utils.io_utils import save

logger = logging.getLogger(__name__)

class Visualizer:
    """
    Génère des visualisations des résultats de simulation
    """
    TEMPLATE = 'plotly_white'

    @staticmethod
    def plot_process_results(
        results: Dict[str, Any],
        node_id: str,
        output_dir: str,
        show: bool = False,
        format: str = 'html'
    ) -> Optional[Path]:
        """
        Génère un graphique complet pour un ProcessNode

        Args:
            results (Dict[str, Any]): Résultats de simulation
            node_id (str): ID du ProcessNode à visualiser
            output_dir (str): Répertoire de sortie
            show (bool, optional): Si True, affiche le graphique à l'écran. Par défaut False
            format (str, optional): Format de sortie ('html', 'png' ou 'both'). Default to 'html'

        Returns:
            Optional[Path]: Chemin du fichier crée, ou None si echec
        """
        history = results.get('history', {})

        if node_id not in history or not history[node_id]:
            logger.warning(f"Aucune donnée pour {node_id}, graphique ignoré")
            return None
        
        flows = history[node_id]
        timestamps = extract_timestamps(flows)
        model_type = flows[0].get('model_type', 'ASM1')

        logger.info(f"Génération du dashboard pour {node_id} (modèle : {model_type})")

        plot_configs = Visualizer._get_plot_configs(model_type)
        rows, cols = create_subplot_layout(len(plot_configs))

        subplot_titles = [config['title'] for config in plot_configs]
        fig = make_subplots(
            rows=rows,
            cols=cols,
            subplot_titles=subplot_titles,
            vertical_spacing=0.12,
            horizontal_spacing=0.10
        )

        for idx, config in enumerate(plot_configs):
            row, col = divmod(idx, cols)
            plotter_cls = get_plotter(config['type'])
            plotter = plotter_cls(fig, flows, timestamps, model_type, row+1, col+1)
            plotter.plot()
            fig.update_yaxes(title_text=config['ylabel'], row=row+1, col=col+1)
            fig.update_xaxes(title_text='Temps', row=row+1, col=col+1)

        fig.update_layout(
            title_text=f"Simulation - {node_id} ({model_type})",
            title_font_size=20,
            showlegend=True,
            template=Visualizer.TEMPLATE,
            height=300*rows,
            width=500*cols
        )

        html_path = save(output_path=Path(output_dir), node_id=node_id, fig=fig, height=300*rows, width=500*cols, format=format)
        
        if show:
            fig.show()

        return html_path
    
    @staticmethod
    def _get_plot_configs(model_type: str) -> List[Dict[str, Any]]:
        """
        Retourne la configuration des graphiques selon le modèle

        Args:
            model_type (str): Type de modèle

        Returns:
            List[Dict[str, Any]]: Liste de configurations de graphiques
        """
        base_configs = [
            {'title': 'DCO (Demande Chimique en Oxygène)', 'type': 'cod', 'ylabel': 'DCO (g/L)'},
            {'title': 'Composés Azotés', 'type': 'nitrogen', 'ylabel': 'Azote (g N/L)'},
            {'title': 'Oxygène Dissous', 'type': 'oxygen', 'ylabel': 'O2 (g/L)'},
            {'title': 'Biomasse Active', 'type': 'biomass', 'ylabel': 'Biomasse (g COD/L)'},
            {'title': 'Substrats Organiques', 'type': 'substrates', 'ylabel': 'Substrat (g COD/L)'}
        ]

        if model_type == 'ASM2D':
            base_configs.append({
                'title': 'Phosphore',
                'type': 'phosphorus',
                'ylabel': 'Phosphore (g P/L)'
            })
        return base_configs
    
    @staticmethod
    def create_dashboard(
        results: Dict[str, Any], 
        output_dir: str,
        format: str = 'html'
    ) -> Dict[str, Path]:
        """
        Crée un dashboard complet avec tous les graphiques

        Args:
            resulsts (Dict[str, Any]): Résultats de simulation
            output_dir (str): Répertoire de sortie
            format (str): Format de sortie ('html', 'png' ou 'both)

        Returns:
            Dict[str, Path]: dictionnaire {node_id: chemin_graphique}
        """
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        dashboard_files = {}

        history = results.get('history', {})

        for node_id in history.keys():
            if node_id == 'influent':
                continue
            plot_path = Visualizer.plot_process_results(
                results,
                node_id,
                str(output_path),
                show=False,
                format=format
            )

            if plot_path:
                dashboard_files[node_id] = plot_path
        
        logger.info(f"Dashboard crée : {len(dashboard_files)} graphiques(s)")

        return dashboard_files