from typing import Any, Dict
from pathlib import Path
from interfaces import ConfigLoader, ResultsExporter, Visualizer
from core import SimulationOrchestrator, ProcessFactory
from .decorators import timed



def create_default_config(output_path: str) -> None:
    """
    Crée une configuration par défaut

    Args:
        output_path (str): Chemin du fichier de sortie
    """
    print("Création d'une configuration par défaut ...")
    ConfigLoader.create_default_config(output_path)
    print(f"Configuration créée : {output_path}")
    print(f"\nPour l'utiliser : python main.py {output_path}")

def load_config(config_path: Path) -> Dict[str, Any]:
    """
    Charge une configuration

    Args:
        config_path (str): Chemin de la configuration à charger

    Returns:
        Dict[str, Any]: _description_
    """
    
    print(f"Chargement de la configuration : {str(config_path)}")
    config = ConfigLoader.load(config_path)
    return config

@timed
def run_simulation(config: Dict[str, Any]) -> Dict[str,Any]:
    """
    Exécute une simulation complète

    Args:
        config (Dict[str, Any]): Configuration de simulation

    Returns:
        Dict[str, Any]: Résultats de la simulation
    """
    sim_name = config.get('name', 'simulation')

    print(f"Initialisation de la simulation '{sim_name}'...")
    orchestrator = SimulationOrchestrator(config)

    print("Création des procédés ...")
    processes = ProcessFactory.create_from_config(config)
    for process in processes:
        orchestrator.add_process(process)
        print(f"\t- {process.name} ({process.node_id})")

    print("Initialisation des procédés ...")
    orchestrator.initialize()

    print("\n"+"="*60)
    print("Simulation en cours ...")
    print("="*60)
    results= orchestrator.run()

    print("\n"+"="*60)
    print("Simulation terminée")
    print("="*60)

    return results

@timed
def export_results(results: Dict[str, Any], with_plots: bool = True) -> Dict[str, Any]:
    """
    Exporte les résultats de simulation

    Args:
        results (Dict[str, Any]): Résultats de simulation
        with_plots (bool, optional): Si True, génère les graphiques. Defaults to True.

    Returns:
        Dict[str, Any]: Informations sur les fichiers exportés
    """
    print("\nExport des résultats ...")
    sim_name = results['metadata'].get('config',{}).get('name','simulation')

    exported = ResultsExporter.export_all(
        results,
        base_dir='output/results',
        name=sim_name
    )

    print(f"\t- Répertoire : {exported['base_directory']}")
    print(f"\t- CSV : {len(exported['files']['csv'])} fichier(s)")
    print(f"\t- JSON : {Path(exported['files']['json']).name}")
    print(f"\t- Résumé : {Path(exported['files']['summary']).name}")

    if with_plots:
        print("\nGénération des graphiques ...")
        dashboard = Visualizer.create_dashboard(
            results,
            output_dir=f"{exported['base_directory']}/figures"
        )
        print(f"\t- {len(dashboard)} graphique(s) créé(s)")
        exported['figures'] = {k: str(v) for k, v in dashboard.items()}

    return exported

def print_summary(results: Dict[str, Any]) -> None:
    """
    Affiche un résumé des résultats

    Args:
        results (dict): Résultats de simulation
    """
    print("\n"+"="*60)
    print("Résumé des résultats")
    print("="*60)
    
    metadata = results.get('metadata', {})
    print(f"\nPériode simulée :")
    print(f"\tDe : {metadata.get('start_time')}")
    print(f"\tA : {metadata.get('final_time')}")
    print(f"\tPas de temps : {metadata.get('timestep')} heures")
    print(f"\tTotal : {metadata.get('steps_completed')} pas")

    stats = results.get('statistics', {})

    if stats:
        print(f"\nStatistiques par procédé : ")
        for node_id, node_stats in stats.items():
            print(f"\n\t{node_id} :")
            print(f"\t\tDebit moyen : {node_stats.get('avg_flowrate', 0):>8.1f} m^3/h")
            print(f"\t\tDCO moyenne:  {node_stats.get('avg_cod', 0):>8.1f} mg/L")
            print(f"\t\tÉchantillons: {node_stats.get('num_samples', 0):>8d}")

    print("\n"+"="*60)

def run_sim_results(config: Dict[str, Any], plots: bool) -> None:
    """
    Appele de fonction

    Args:
        config (Dict[str, Any]): Configuration de simulation
        plots (bool): Création des graphiques
    """
    results = run_simulation(config)
    exported = export_results(results, with_plots=not plots)
    print("\nTraitement terminé avec succès !")
    print(f"\nRésultats disponibles dans : {exported['base_directory']}")
    print_summary(results)