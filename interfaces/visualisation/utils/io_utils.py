import plotly.graph_objects as go
import logging

from typing import Optional
from pathlib import Path

logger = logging.getLogger(__name__)

def ensure_dir(path: Path):
    path.mkdir(parents=True, exist_ok=True)

def save(output_path: Path, node_id: str, fig: go.Figure, height: int, width: int, format: str='html') -> Optional[Path]:
    """
    Sauvegarde les plots de simulation

    Args:
        output_path (Path): Chemin de sortie
        node_id (str): ID du ProcessNode
        fig (go.Figure): Graphique qu'on souhaite sauvegarder
        format (str, optional): Format de sortie ('html', 'png' ou 'both'). Default to 'html'

    Returns:
        Optional[Path]: Chemin du fichier crée, ou None si echec
    """
    ensure_dir(output_path)

    html_path = output_path / f'{node_id}_dashboard.html'

    if format in ['html', 'both']:
        fig.write_html(html_path)
        logger.info(f"Dashboard HTML sauvegardé : {html_path}")

    if format in ['png', 'both']:
        png_path = output_path / f'{node_id}_dashboard.png'
        try:
            fig.write_image(png_path, width=width, height=height)
            logger.info(f"Dashboard PNG sauvegardé : {png_path}")
        except Exception as e:
            logger.warning(f"Impossible de sauvegarder en PNG : {e}")

    return html_path
