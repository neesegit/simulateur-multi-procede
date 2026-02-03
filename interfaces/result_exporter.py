"""
Module d'export des résultat de simulation

Rôle :
- Exporter les résultats en CSV
- Exporter en JSON
- Sauvegarder les métadonnées
"""
import json
import pandas as pd
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime
import logging

from core.registries.export_registry import ExportRegistry

logger = logging.getLogger(__name__)

class ResultsExporter:
    """
    Gère l'export des résultats de simulation dans différents formats
    """

    @staticmethod
    def export_to_csv(results: Dict[str, Any], output_dir: str) -> Dict[str, Path]:
        """
        Exporte les résultats en fichiers CSV (un par ProcessNode)

        Args:
            results (Dict[str, Any]): Résultats de simulation
            output_dir (str): Répertoire de sortie

        Returns:
            Dict[str, Path]: Dictionnaire{node_id: chemin_csv}
        """
        registry = ExportRegistry.get_instance()
        output_path = Path(output_dir)

        history = results.get('history', {})
        exported_files = {}

        for node_id, flows in history.items():
            if node_id == 'influent':
                continue
            if not flows:
                logger.warning(f"Aucune donnée pour {node_id}, export CSV ignoré")
                continue

            try:
                filepath = registry.export(
                    format_name='csv',
                    results=results,
                    output_path=output_path,
                    node_id=node_id
                )
                exported_files[node_id] = filepath
                logger.info(f"CSV exporté : {filepath}")
            except Exception as e:
                logger.error(f"Erreur export CSV pour {node_id}: {e}")

        return exported_files
    
    @staticmethod
    def export_to_json(results: Dict[str, Any], output_path: str) -> Path:
        """
        Exporte tous les résultats en un seul fichier JSON

        Args:
            results (Dict[str, Any]): Résultats de simulation
            output_path (str): Chemin du fichier de sortie

        Returns:
            Path: Chemin du fichier crée
        """
        registry = ExportRegistry.get_instance()
        path = Path(output_path)

        try:
            sim_name = results['metadata'].get('sim_name', 'simulation')
            filepath = registry.export(
                format_name='json',
                results=results,
                output_path=path.parent,
                name=sim_name
            )
            logger.info(f"JSON exporté : {filepath}")
            return filepath
        except Exception as e:
            logger.error(f"Erreur export JSON : {e}")
            raise

    @staticmethod
    def export_summary(results: Dict[str, Any], output_path: str) -> Path:
        """
        Exporte un résumé des résultats en fichier texte

        Args:
            results (Dict[str, Any]): Résultats de simulation
            output_path (str): Chemin du fichier de sortie

        Returns:
            Path: Chemin du fichie crée
        """
        path = Path(output_path)
        path.parent.mkdir(parents=True, exist_ok=True)

        metadata = results.get('metadata', {})
        stats = results.get('statistics', {})

        with open(path, 'w') as f:
            f.write("="*70+"\n")
            f.write("Résumé de la simulation\n")
            f.write("="*70+"\n\n")

            # Métadonnées
            f.write("Paramètres de la simulation:\n")
            f.write(f"\t- Début : {metadata.get('start_time')}\n")
            f.write(f"\t- Fin : {metadata.get('final_time')}\n")
            f.write(f"\t- Pas de temps : {metadata.get('timestep')} heures\n")
            f.write(f"\t- Nombre de pas : {metadata.get('steps_completed')}\n\n")

            # Statistiques par procédé
            f.write("-"*70+"\n")
            f.write("Statistiques par procédé\n")
            f.write("-"*70+"\n\n")

            for node_id, node_stats in stats.items():
                f.write(f"{node_id} : \n")
                f.write(f"\t- Débit moyen : {node_stats.get('avg_flowrate', 0):.1f} m^3/h\n")
                f.write(f"\t- DCO moyenne : {node_stats.get('avg_cod', 0):.1f} mg/L\n")
                if node_id != 'influent':
                    f.write(f"\t- Echantillons : {node_stats.get('num_samples', 0)}\n\n")
                else: f.write("\n\n")

            f.write("="*70+"\n")
        
        logger.info(f"Résumé exporté : {path}")
        return path
    
    @staticmethod
    def export_all(results: Dict[str, Any],
                   base_dir: str,
                   name: Optional[str] = None) -> Dict[str, Any]:
        """
        Exporte tous les formats à la fois dans un répertoire dédie

        Args:
            results (Dict[str, Any]): Résultats de simulation
            base_dir (str): Répertoire de base
            name (str, optional): Nom de la simulation (optionnel)

        Returns:
            Dict[str, Any]: Dictionnaire contenant les chemins de tous les fichiers exportés
        """
        if name is None:
            name = f"simulation_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        # Crée un sous-répertoire pour cette simulation
        sim_dir = Path(base_dir) / name
        sim_dir.mkdir(parents=True, exist_ok=True)

        exported = {
            'simulation_name': name,
            'base_directory': str(sim_dir),
            'files': {}
        }

        # Export CSV
        csv_files = ResultsExporter.export_to_csv(results, str(sim_dir/'csv'))
        exported['files']['csv'] = {k: str(v) for k, v in csv_files.items()}

        # Export JSON complet
        json_path = ResultsExporter.export_to_json(
            results,
            str(sim_dir / f'{name}_full.json')
        )
        exported['files']['json'] = str(json_path)

        # Export résumé texte
        summary_path = ResultsExporter.export_summary(
            results,
            str(sim_dir / f'{name}_summary.txt')
        )
        exported['files']['summary'] = str(summary_path)

        logger.info(f"Tous les résulstats exportés dans : {sim_dir}")

        return exported