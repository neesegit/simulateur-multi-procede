import logging

from typing import Any, Dict, Optional
from pathlib import Path

from interfaces.config import ConfigLoader 
from interfaces import ResultsExporter, Visualizer
from interfaces.metrics_exporter import MetricsExporter
from core.orchestrator.simulation_orchestrator import SimulationOrchestrator 
from core.process.process_factory import ProcessFactory
from utils.decorators import timed
from core.calibration.calibration_manager import CalibrationManager
from core.calibration.calibration_result import CalibrationResult

logger = logging.getLogger(__name__)

def run_sim_with_calibration(
        config: Dict[str, Any],
        plots: bool = True,
        calibration_mode: str = 'auto',
        interactive: bool = False
    ) -> Optional[Dict[str, Any]]:
    """
    Lance une simulation avec gestion automatique de la calibration

    Args:
        config (Dict[str, Any]): Configuration de simulation
        plots (bool, optional): Générer les graphiques. Defaults to True.
        calibration_mode (str, optional): 'auto' (valide), 'skip' (ignore), 'force' (recalibrer). Defaults to 'auto'.
        interactive (bool, optional): Demander confirmation avant chaque étape. Defaults to False.

    Returns:
        Optional[Dict[str, Any]]: Résultats de simulation ou None si erreur
    """
    print("\n"+"="*70)
    print("Workflow simulation")
    print("="*70)

    #TODO : calibration pour variation d'influent
    # print("\nGestion de la calibration")

    # try:
    #     calib_manager = CalibrationManager(config)

    #     match calibration_mode:
    #         case 'skip':
    #             skip_existing = True
    #         case _:
    #             skip_existing = False
        
    #     calibration_results = calib_manager.run_all(
    #         skip_if_exists=skip_existing,
    #         interactive=interactive
    #     )

    #     failed_calib = [
    #         pid for pid, result in calibration_results.items()
    #         if result is None
    #     ]

    #     if failed_calib:
    #         logger.warning(
    #             f"Calibration échouée pour : {', '.join(failed_calib)}"
    #         )
    # except Exception as e:
    #     logger.error(f"Erreur lors de la calibration : {e}")
    #     print(f"Erreur : {e}")
    #     if not interactive:
    #         raise

    print("\nPréparation de la simulation")

    try:
        results = run_simulation(config)
    except Exception as e:
        logger.error(f"Erreur lors de la simulation : {e}")
        print(f"Erreur : {e}")
        raise

    print("\nExport et visualisation")
    try:
        exported = export_results(results, with_plots=plots)
        print(f"\nRésultats disponibles dans : {exported['base_directory']}")
    except Exception as e:
        logger.error(f"Erreur lors de l'export : {e}")
        print(f"Export partiel : {e}")
    
    print_summary(results)
    return results

@timed
def run_simulation(config: Dict[str, Any]) -> Dict[str,Any]:
    """
    Exécute une simulation complète

    Args:
        config (Dict[str, Any]): Configuration de simulation

    Returns:
        Dict[str, Any]: Résultats de la simulation
    """
    #calibration_results['activatedsludge_1'].metadata.config_hash
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
    results = orchestrator.run()

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
    sim_name = results['metadata'].get('sim_name','simulation')

    exported = ResultsExporter.export_all(
        results,
        base_dir='output/results',
        name=sim_name
    )
    print("\nExport des métriques de performance ...")
    metrics_json = MetricsExporter.export_performance_metrics(
        results,
        output_dir=f"{exported['base_directory']}/metrics"
    )
    print(f"\t- Métriques JSON : {metrics_json.name}")

    metrics_csv = MetricsExporter.export_performance_csv(
        results,
        output_dir=f"{exported['base_directory']}/metrics"
    )
    print(f"\t- Métriques CSV : {len(metrics_csv)} fichier(s)")

    report_path = MetricsExporter.create_performance_report(
        results,
        output_path=f"{exported['base_directory']}/performance_report.txt"
    )
    print(f"\t- Rapport : {report_path.name}")

    exported['files']['metrics_json'] = str(metrics_json)
    exported['files']['metrics_csv'] = {k: str(v) for k, v in metrics_csv.items()}
    exported['files']['performance_report'] = str(report_path)

    print(f"\t- Répertoire : {exported['base_directory']}")
    print(f"\t- CSV : {len(exported['files']['csv'])} fichier(s)")
    print(f"\t- JSON : {Path(exported['files']['json']).name}")
    print(f"\t- Résumé : {Path(exported['files']['summary']).name}")

    if with_plots:
        print("\nGénération des graphiques ...")
        dashboard = Visualizer.create_dashboard(
            results,
            output_dir=f"{exported['base_directory']}/figures",
            format='both'
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
    print(f"\tA : {metadata.get('end_time')}")
    print(f"\tPas de temps : {metadata.get('timestep')} heures")
    print(f"\tTotal : {metadata.get('steps_completed')} pas")

    stats = results.get('statistics', {})

    if stats:
        print(f"\nStatistiques par procédé : ")
        for node_id, node_stats in stats.items():
            print(f"\n\t{node_id} :")
            print(f"\t\tDebit moyen : {node_stats.get('avg_flowrate', 0):>8.1f} m^3/h")
            print(f"\t\tDCO moyenne :  {node_stats.get('avg_cod', 0):>8.1f} mg/L")
            if node_id != 'influent':
                print(f"\t\tÉchantillons : {node_stats.get('num_samples', 0):>8d}")

    print("\n"+"="*60)

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