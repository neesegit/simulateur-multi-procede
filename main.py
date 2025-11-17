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
import sys
from pathlib import Path

from utils.cli_runner import cli_config, parse_arguments
from utils.decorators import safe_run
from utils.logging_utils import setup_logging
from utils.directory_utils import setup_directories
from core.sim_runner import run_sim_results, load_config

@safe_run
def main() -> int:
    args = parse_arguments()
    logger = setup_logging(args.log_level)
    setup_directories()

    print("""
    ╔══════════════════════════════════════════════════════════╗
    ║              SIMULATEUR MULTI-PROCEDES                   ║
    ╚══════════════════════════════════════════════════════════╝
    """)

    if args.interactive:
        config_dict = cli_config()

        if not config_dict.get('_launch'):
            print("\nConfiguration terminée")
            return 0
        logger.info("Utilisation de la configuration interactive")

        run_sim_results(config_dict, args.no_plots)
        return 0
    
    # Vérifie que la config existe
    config_path = Path(args.config)
    if not config_path.exists():
        logger.warning(f"Configuration introuvable : {config_path}")
        print(f"\nLe fichier {config_path} n'existe pas")
        return 1
        
    config = load_config(config_path)
    run_sim_results(config, args.no_plots)
    return 0

if __name__ == '__main__':
    sys.exit(main())