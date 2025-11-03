import argparse
import sys

from typing import Dict, Any
from interfaces.cli.cli_interface import CLIInterface

def parse_arguments() -> argparse.Namespace:
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
    python main.py                                      # Menu d'aide
    python main.py config/my_sim.json                   # Config spécifique
    python main.py --no-plots                           # Sans graphiques
    python main.py --log-level DEBUG                    # Mode debug
"""
    )

    parser.add_argument(
        'config',
        nargs='?',
        default='config/example_asm1.json',
        help='Chemin vers le fichier de configuration (ex : config/example.json)'
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

    if len(sys.argv) == 1:
        parser.print_help()
        sys.exit(0)

    return parser.parse_args()

def cli_config() -> Dict[str, Any]:
    print("Mode interactif activé\n")
    cli = CLIInterface()
    config_dict = cli.run()
    return config_dict
