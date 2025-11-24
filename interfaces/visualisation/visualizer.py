"""
Module de visualisation des résultats de simulation - point d'entrée principal
"""
import logging 

from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime

from .visualizer_factory import VisualizerFactory

logger = logging.getLogger(__name__)

def extract_timestamps(flows) -> List[datetime]:
    return [datetime.fromisoformat(f["timestamp"]) for f in flows]

class Visualizer:
    """
    Point d'entrée principal pour la visualisation. Délègue au visualiseur approprié selon le modèle
    """

    @staticmethod
    def plot_process_results(
        results: Dict[str, Any],
        node_id: str,
        output_dir: str,
        show: bool = False,
        format: str = 'html'
    ) -> Optional[Path]:
        """
        Génère un dashboard pour un ProcessNode

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
        model_type = flows[0].get('model_type', 'ASM1')

        visualizer = VisualizerFactory.create(model_type)
        if visualizer is None:
            logger.error(
                f"Impossible de créer un visualiseur pour {model_type}. "
                f"Visualisation ignorée pour {node_id}."
            )
            return None
        
        timestamps = extract_timestamps(flows)

        logger.info(f"Génération du dashboard pour {node_id} ({model_type})")

        try:
            saved_path = visualizer.create_dashboard(
                flows=flows,
                timestamps=timestamps,
                output_dir=output_dir,
                node_id=node_id,
                show=show,
                format=format
            )

            logger.info(f"Dashboard crée : {saved_path}")
            return saved_path
        
        except Exception as e:
            logger.error(f"Erreur lors de la création du dashboard : {e}", exc_info=True)
            return None
        
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