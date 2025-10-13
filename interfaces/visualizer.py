"""
Module de visualisation des résultats de simulation

Rôle :
- Générer des graphiques de simulation
- Créer des dashboards comparatifs
- Sauvegarder les figures
"""
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional
import logging 
import numpy as np

logger = logging.getLogger(__name__)

class Visualizer:
    """
    Génère des visualisations des résultats de simulation
    """

    # Configuration par défaut des styles
    STYLE_CONFIG = {
        'figure.figsize': (15,10),
        'font.size': 10,
        'axes.titlesize': 12,
        'axes.labelsize': 11,
        'xtick.labelsize': 9,
        'ytick.labelsize': 9,
        'legend.fontsize': 9,
        'figure.dpi': 100
    }

    # Couleurs pour les différents composants
    COLORS = {
        'cod': '#1f77b4',      # Bleu
        'snh': '#d62728',      # Rouge
        'sno': '#2ca02c',      # Vert
        'so': '#ff7f0e',       # Orange
        'ss': '#9467bd',       # Violet
        'xbh': '#8c564b',      # Marron
        'xba': '#e377c2',      # Rose
        'biomass': '#7f7f7f'   # Gris
    }

    @staticmethod
    def plot_process_results(results: Dict[str, Any],
                             node_id: str,
                             output_dir: str,
                             show: bool = False) -> Optional[Path]:
        """
        Génère un graphique complet pour un ProcessNode

        Args:
            results (Dict[str, Any]): Résultats de simulation
            node_id (str): ID du ProcessNode à visualiser
            output_dir (str): Répertoire de sortie
            show (bool, optional): Si True, affiche le graphique à l'écran. Par défaut False

        Returns:
            Optional[Path]: Chemin du fichier crée, ou None si echec
        """
        history = results.get('history', {})

        if node_id not in history or not history[node_id]:
            logger.warning(f"Aucune donnée pour {node_id}, graphique ignoré")
            return None
        
        flows = history[node_id]

        # Extrait les données temporelles
        timestamps = [datetime.fromisoformat(f['timestamp']) for f in flows]

        # Applique le style
        plt.style.use('seaborn-v0_8-darkgrid')
        
        # crée la figure avec sous-graphique
        fig, axes = plt.subplots(3,2, figsize=(15,12))
        fig.suptitle(f'Simulation - {node_id}', fontsize=16, fontweight='bold')

        # --- Graphique 1 : DCO ---
        Visualizer._plot_cod(axes[0,0], timestamps, flows)

        # --- Graphique 2 : Azote (NH4, NO3) ---
        Visualizer._plot_nitrogen(axes[0,1], timestamps, flows)

        # --- Graphique 3 : Oxygène dissous ---
        Visualizer._plot_oxygen(axes[1,0], timestamps, flows)

        # --- Graphique 4 : Biomasse ---
        Visualizer._plot_biomass(axes[1,1], timestamps, flows)

        # --- Graphique 5 : Substrats ---
        Visualizer._plot_substrates(axes[2,0], timestamps, flows)

        # --- Graphique 6 : Débit & Température ---
        Visualizer._plot_operational(axes[2,1], timestamps, flows)

        # Ajuste le layout
        plt.tight_layout()

        # Sauvegarde
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        plot_path = output_path / f"{node_id}_complete.png"
        plt.savefig(plot_path, dpi=300, bbox_inches='tight')
        logger.info(f"Graphique sauvegardé : {plot_path}")

        if show:
            plt.show()
        else:
            plt.close()

        return plot_path
        
    @staticmethod
    def _plot_cod(ax, timestamps, flows):
        """Graphique DCO"""

        cod_values = [f.get('cod',0) for f in flows]

        if any(cod_values):
            ax.plot(timestamps, cod_values,
                    color=Visualizer.COLORS['cod'],
                    linewidth=2,
                    label='DCO totale')
            ax.set_ylabel('DCO (mg/L)', fontweight='bold')
            ax.set_title('Demande Chimique en Oxygène')
            ax.grid(True, alpha=0.3)
            ax.legend()

            # Format des dates
            ax.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M'))
            ax.tick_params(axis='x', rotation=45)

    @staticmethod
    def _plot_nitrogen(ax, timestamps, flows):
        """Graphique Azote (NH4 et NO3)"""
        components = flows[0].get('components', {})

        if 'snh' in components:
            snh_values = [f.get('components', {}).get('snh',0) for f in flows]
            ax.plot(timestamps, snh_values,
                    color=Visualizer.COLORS['snh'],
                    linewidth=2,
                    label='NH4-N')
            
        if 'sno' in components:
            sno_values = [f.get('components', {}).get('sno',0) for f in flows]
            ax.plot(timestamps, sno_values,
                    color=Visualizer.COLORS['sno'],
                    linewidth=2,
                    label='NO3-N')
            
        ax.set_ylabel('Azote (mg N/L)', fontweight='bold')
        ax.set_title('Composés azotés')
        ax.grid(True, alpha=0.3)
        ax.legend()
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M'))
        ax.tick_params(axis='x', rotation=45)

    @staticmethod
    def _plot_oxygen(ax, timestamps, flows):
        """Graphique Oxygène dissous"""
        components = flows[0].get('components', {})
        
        if 'so' in components:
            so_values = [f.get('components', {}).get('so', 0) for f in flows]
            ax.plot(timestamps, so_values, 
                   color=Visualizer.COLORS['so'], 
                   linewidth=2, 
                   label='DO mesuré')
            
            # Ajoute la consigne si disponible
            ax.axhline(y=2.0, color='red', linestyle='--', 
                      linewidth=1.5, label='Consigne', alpha=0.7)
            
            ax.set_ylabel('Oxygène dissous (mg O2/L)', fontweight='bold')
            ax.set_title('Oxygène dissous')
            ax.grid(True, alpha=0.3)
            ax.legend()
            ax.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M'))
            ax.tick_params(axis='x', rotation=45)
    
    @staticmethod
    def _plot_biomass(ax, timestamps, flows):
        """Graphique Biomasse"""
        components = flows[0].get('components', {})
        
        if 'xbh' in components and 'xba' in components:
            xbh_values = [f.get('components', {}).get('xbh', 0) for f in flows]
            xba_values = [f.get('components', {}).get('xba', 0) for f in flows]
            
            # Biomasse totale
            total_biomass = [xbh + xba for xbh, xba in zip(xbh_values, xba_values)]
            
            ax.fill_between(timestamps, 0, xbh_values, 
                          color=Visualizer.COLORS['xbh'], 
                          alpha=0.6, 
                          label='Hétérotrophes')
            ax.fill_between(timestamps, xbh_values, total_biomass, 
                          color=Visualizer.COLORS['xba'], 
                          alpha=0.6, 
                          label='Autotrophes')
            
            ax.plot(timestamps, total_biomass, 
                   color='black', 
                   linewidth=1.5, 
                   linestyle='--', 
                   label='Total')
            
            ax.set_ylabel('Biomasse (mg DCO/L)', fontweight='bold')
            ax.set_title('Biomasse active')
            ax.grid(True, alpha=0.3)
            ax.legend()
            ax.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M'))
            ax.tick_params(axis='x', rotation=45)
    
    @staticmethod
    def _plot_substrates(ax, timestamps, flows):
        """Graphique Substrats"""
        components = flows[0].get('components', {})
        
        if 'ss' in components:
            ss_values = [f.get('components', {}).get('ss', 0) for f in flows]
            ax.plot(timestamps, ss_values, 
                   color=Visualizer.COLORS['ss'], 
                   linewidth=2, 
                   label='SS (rapidement biodégradable)')
        
        if 'xs' in components:
            xs_values = [f.get('components', {}).get('xs', 0) for f in flows]
            ax.plot(timestamps, xs_values, 
                   color='brown', 
                   linewidth=2, 
                   label='XS (lentement biodégradable)')
        
        ax.set_ylabel('Substrat (mg DCO/L)', fontweight='bold')
        ax.set_title('Substrats organiques')
        ax.grid(True, alpha=0.3)
        ax.legend()
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M'))
        ax.tick_params(axis='x', rotation=45)
    
    @staticmethod
    def _plot_operational(ax, timestamps, flows):
        """Graphique Paramètres opérationnels"""
        flowrates = [f.get('flowrate', 0) for f in flows]
        temps = [f.get('temperature', 0) for f in flows]
        
        # Double axe Y
        ax2 = ax.twinx()
        
        line1 = ax.plot(timestamps, flowrates, 
                       color='blue', 
                       linewidth=2, 
                       label='Débit')
        ax.set_ylabel('Débit (m^3/h)', color='blue', fontweight='bold')
        ax.tick_params(axis='y', labelcolor='blue')
        
        line2 = ax2.plot(timestamps, temps, 
                        color='red', 
                        linewidth=2, 
                        label='Température')
        ax2.set_ylabel('Température (°C)', color='red', fontweight='bold')
        ax2.tick_params(axis='y', labelcolor='red')
        
        ax.set_title('Paramètres opérationnels')
        ax.grid(True, alpha=0.3)
        
        # Combine les légendes
        lines = line1 + line2
        labels = [l.get_label() for l in lines]
        ax.legend(lines, labels, loc='upper left')
        
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M'))
        ax.tick_params(axis='x', rotation=45)

    @staticmethod
    def plot_comparison(results_list: List[Dict[str, Any]],
                        labels: List[str],
                        node_id: str,
                        output_path: str,
                        metric: str = 'cod') -> Path:
        """
        Compare plusieurs simulation sur un même graphique

        Args:
            results_list (List[Dict[str, Any]]): Liste de résultats de simulation
            labels (List[str]): Labels pour chaque simulation
            node_id (str): ID du ProcessNode à comparer
            output_path (str): Chemin du fichier de sortie
            metric (str, optional): Métrique à comparer ('cod', 'snh', 'biomass' etc). Defaults to 'cod'.

        Returns:
            Path: Chemin du fichier crée
        """
        plt.figure(figsize=(12,6))

        for results, label in zip(results_list, labels):
            history = results.get('history', {})

            if node_id not in history:
                continue

            flows = history[node_id]
            timestamps = [datetime.fromisoformat(f['timestamp']) for f in flows]

            # Extrait la métrique
            if metric == 'cod':
                values = [f.get('cod',0) for f in flows]
                ylabel = 'DCO (mg/L)'
            elif metric == 'snh':
                values = [f.get('components',{}).get('snh',0) for f in flows]
                ylabel = 'NH4-N (mg/L)'
            elif metric == 'biomass':
                values = [f.get('components',{}).get('xbh',0) +
                          f.get('components',{}).get('xba',0) for f in flows]
                ylabel = 'Biomasse (mg DCO/L)'
            else:
                values = [f.get('components', {}).get(metric, 0) for f in flows]
                ylabel = f'{metric} (mg/L)'
            
            plt.plot(timestamps, values, linewidth=2, label=label) # pyright: ignore[reportArgumentType]

        plt.xlabel('Temps')
        plt.ylabel(ylabel) # pyright: ignore[reportPossiblyUnboundVariable]
        plt.title(f'Comparaison - {metric.upper()} - {node_id}')
        plt.legend()
        plt.grid(True, alpha=0.3)
        plt.tight_layout()

        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        logger.info(f"Graphique de comparaison sauvegardé : {output_path}")
        plt.close()

        return Path(output_path)
    
    @staticmethod
    def create_dashboard(results: Dict[str, Any], output_dir: str) -> Dict[str, Path]:
        """
        Crée un dashboard complet avec tous les graphiques

        Args:
            resulsts (Dict[str, Any]): Résultats de simulation
            output_dir (str): Répertoire de sortie

        Returns:
            Dict[str, Path]: dictionnaire {node_id: chemin_graphique}
        """
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        dashboard_files = {}

        history = results.get('history', {})

        for node_id in history.keys():
            plot_path = Visualizer.plot_process_results(
                results,
                node_id,
                str(output_path),
                show=False
            )

            if plot_path:
                dashboard_files[node_id] = plot_path
        
        logger.info(f"Dashboard crée : {len(dashboard_files)} graphiques(s)")

        return dashboard_files