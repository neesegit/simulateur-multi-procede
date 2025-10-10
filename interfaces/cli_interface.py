"""
Interface CLI interactive pour configurer et lancer des simulations

Usage directe :
    python -m interfaces.cli_interface

Permet de :
- Sélectionner les procédés à simuler
- Choisir l'ordre des procédés
- Configurer les paramètres de chaque procédé
- Définir les conditions initiales
- Sauvegarder la configuration
- Lancer la simulation
"""
import sys
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import json
from pathlib import Path

from .config_loader import ConfigLoader

class CLIInterface:
    """
    Interface en ligne de commande interactive pour le simulateur
    """

    # Catalogue des procédés disponibles
    AVAILABLE_PROCESSES = {
        '1': {
            'type': 'ASM1Process',
            'name': 'Boues activées (ASM1)',
            'description': 'Traitement biologique par boues activées',
            'required_params': ['volume', 'dissolved_oxygen_setpoint'],
            'optional_params': ['depth', 'recycle_ratio', 'waste_ratio']
        },
        # Ajoutez ici d'autre procédés plus tard : TODO
    }

    # Paramètres par défaut pour chaque type de procédé
    DEFAULT_PARAMS = {
        'ASM1Process': {
            'volume': 5000.0,
            'depth': 4.0,
            'dissolved_oxygen_setpoint': 2.0,
            'recycle_ratio': 1.0,
            'waste_ratio': 0.01
        }
    }

    def __init__(self):
        """Initialise l'interface CLI"""
        self.config = {
            'name': '',
            'description': '',
            'simulation': {},
            'influent': {},
            'processes': []
        }

    def run(self) -> Dict[str, Any]:
        """
        Lance l'interface interactive complète

        Returns:
            Dict[str, Any]: Configuration créée
        """
        self.print_welcome()

    def print_welcome():
        """Affiche le message de bienvenue"""
        print("\n" + "="*70)
        print(" "*15 + "CONFIGURATION INTERACTIVE DU SIMULATEUR STEP")
        print("="*70)
        print("\nCe guide vous aidera à configurer votre simulation pas à pas.")
        print("Appuyez sur Entrée pour utiliser les valeurs par défaut [entre crochets].")
        print("="*70 + "\n")

    def configure_general(self):
        """Configure les informatiosn générales"""
        print("\n"+"-"*70)
        print("ETAPE 1/7 : Informations générales")
        print("-"*70)

        default_name = f"simulation_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        name = input(f"\nNom de la simulation [{default_name}] : ").strip()
        self.config['name'] = name if name else default_name

        description = input("Description (optionnel) : ").strip()
        self.config['description'] = description if description else "Simulation créée via CLI"

        print(f"\nSimulation créée : {self.config['name']}")

    def configure_simulation_time(self):
        """Configure les paramètres temporels"""
        print("\n" + "-"*70)
        print("ETAPE 2/7 : Paramètres temporels")
        print("-"*70)

        # Date de début
        default_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        start_input = input(f"\nDate de début [YYYY-MM-DD] [{default_start.date()}] : ").strip()

        if start_input:
            try:
                start_time = datetime.isoformat(start_input+"T00:00:00")
            except:
                print("Format invalide, utilisation de la date par défaut")
                start_time = default_start
        else:
            start_time = default_start

        # Durée
        print("\nDurée de la simulation :")
        duration_days = self.ask


# ============= Methode utilitaire ================
    def ask_number(self, prompt: str, default: float,
                   min_val: Optional[float] = None,
                   max_val: Optional[float] = None) -> float:
        