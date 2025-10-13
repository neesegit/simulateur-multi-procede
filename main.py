"""
Point d'entrée principal du simulateur

Usage :
    python main.py                                  # Config par défaut
    python main.py config/my_sim.json               # Config spécifique
    python main.py --create-config config/new.json  # Crée un config
    python main.py --help                           # Aide

Exemples :
    # Simulation simple
    python main.py
    
    # Simulation avec config personnalisée
    python main.py config/scenario_high_load.json
    
    # Créer une nouvelle config
    python main.py --create-config config/my_new_config.json
"""
import argparse
import logging
from pathlib import Path
import sys

from interfaces import ConfigLoader, ResultsExporter, Visualizer
from core.orchestrator import SimulationOrchestrator
from core.process_factory import ProcessFactory

# Configuration du logging
def setup_logging(log_level: str = "INFO"):
    """Configure le système de logging"""
    Path('output/logs').mkdir(parents=True, exist_ok=True)

    numeric_level = getattr(logging, log_level.upper(), logging.INFO)

    logging.basicConfig(
        level=numeric_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('output/logs/simulation.log'),
            logging.StreamHandler()
        ]
    )

logger = logging.getLogger(__name__)

def print_banner():
    """Affiche la bannière de démarrage"""
    print("""
    ╔══════════════════════════════════════════════════════════╗
    ║                     SIMULATEUR                           ║
    ║                    Version OUI                           ║
    ╚══════════════════════════════════════════════════════════╝
    """)

def setup_directories():
    """Crée la structure de répertoires nécessaire"""
    directories = [
        'output/results',
        'output/logs',
        'output/figures',
        'config',
        'data/raw',
        'data/processed'
    ]
    for dir_path in directories:
        Path(dir_path).mkdir(parents=True, exist_ok=True)
    
    logger.debug("Structure de répertoires initialisée")

def create_config(output_path: str):
    """
    Crée une configuration par défaut

    Args:
        output_path (str): Chemin du fichier de sortie
    """
    print("Création d'une configuration par défaut ...")
    config = ConfigLoader.create_default_config(output_path)
    print(f"Configuration créée : {output_path}")
    print(f"\nPour l'utiliser : python main.py {output_path}")
    return 0

def run_simulation(config_path: str, with_plots: bool = True) -> dict:
    """
    Exécute une simulation complète

    Args:
        config_path (str): Chemin vers le fichier de configuration
        with_plots (bool, optional): Si True, génère les graphiques

    Returns:
        dict: Résultats de la simulation
    """
    print(f"Chargement de la configuration : {config_path}")
    config = ConfigLoader.load(config_path)
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

def export_results(results: dict, with_plots: bool = True) -> dict:
    """
    Exporte les résultats de simulation

    Args:
        results (dict): Résultats de simulation
        with_plots (bool, optional): Si True, génère les graphiques. Defaults to True.

    Returns:
        dict: Informations sur les fichiers exportés
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

def print_summary(results: dict):
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

def parse_arguments():
    """
    Parse les arguments de ligne de commande

    Returns:
        Arguments parsés
    """
    parser = argparse.ArgumentParser(
        description='Simulateur',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemples d'utilisation :
    python main.py                                      # Config par défaut
    python main.py config/my_sin.json                   # Config spécifique
    python main.py --no-plots                           # Sans graphiques
    python main.py --create-config config/new.json      # Crée config
    python main.py --log-level DEBUG                    # Mode debug
"""
    )

    parser.add_argument(
        'config',
        nargs='?',
        default='config/example_asm1.json',
        help='Chemin vers le fichier de configuration (défaut : config/example_asm1.json)'
    )

    parser.add_argument(
        '--create-config',
        metavar='PATH',
        help='Crée une configuration par défaut au chemin spécifié'
    )

    parser.add_argument(
        '--no-plots',
        action='store_true',
        help='Ne génère pas de graphiques (plus rapide)'
    )

    parser.add_argument(
        '--log-level',
        choices=['DEBUG','INFO','WARNING','ERROR'],
        default='INFO',
        help='Niveau de logging (défaut : INFO)'
    )

    parser.add_argument(
        '--interactive',
        '-i',
        action='store_true',
        help='Mode interactif : configure la simulation via CLI'
    )

    return parser.parse_args()

def main():
    args = parse_arguments()

    # Configure le logging
    setup_logging(args.log_level)

    # Affiche la bannière
    print_banner()

    try:
        # Prépare l'environnement
        setup_directories()

        # Mode création de config
        if args.interactive:
            from interfaces.cli_interface import CLIInterface

            print("Mode interactif activé\n")
            cli = CLIInterface()
            config_dict = cli.run()

            # Si l'utilisateur ne veut pas lancer maintenant
            if not config_dict.get('_launch'):
                print("\nConfiguration terminée")
                return 0
            
            # Sinon, on utilise la config créée
            logger.info("Utilisation de la configuration interactive")

            # Crée l'orchestrator directemetn avec le dict
            orchestrator = SimulationOrchestrator(config_dict)
            processes = ProcessFactory.create_from_config(config_dict)
            for process in processes:
                orchestrator.add_process(process)

            orchestrator.initialize()
            results = orchestrator.run()

            # Exporte
            exported = export_results(results, with_plots=not args.no_plots)
            print_summary(results)

            print(f"\nRésultats disponibles dans : {exported['base_directory']}")
            return 0
        
        # Mode création de config
        if args.create_config:
            return create_config(args.create_config)
        
        # Vérifie que la config existe (sauf si création d'une par défaut)
        config_path = Path(args.config)
        if not config_path.exists():
            logger.warning(f"Configuration introuvable : {config_path}")
            print(f"\nLe fichier {config_path} n'existe pas")

            # Propose de créer une config par défaut
            response = input("\nVoulez-vous créer une configuration par défaut ? (O/n) : ")
            if response.lower() in ['','o','oui','y','yes']:
                config_path.parent.mkdir(parents=True, exist_ok=True)
                ConfigLoader.create_default_config(str(config_path))
                print(f"Configuration créée : {config_path}")
            else:
                print("\nAbandon")
                return 1
            
        # Lance la simulation
        results = run_simulation(str(config_path), with_plots=not args.no_plots)

        # Exporte les résultats
        exported = export_results(results, with_plots=not args.no_plots)

        # Affiche le résumé
        print_summary(results)

        # Message de fin
        print("\nTraitement terminé avec succès !")
        print(f"\nRésultats disponibles dans : {exported['base_directory']}")

        return 0
    
    except KeyboardInterrupt:
        logger.warning("Simulation interrompue par l'utilisateur")
        print("\n\nSimulation interrompue")
        return 1
    
    except Exception as e:
        logger.error(f"Erruer fatale : {e}", exc_info=True)
        print(f"\n\nErreur : {e}")
        print("\nConsultez le fichier output/logs/simulation.log pour plus de détails")
        return 1
    
if __name__ == '__main__':
    sys.exit(main())