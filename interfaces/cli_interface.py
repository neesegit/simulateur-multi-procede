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
from typing import Dict, Any
from .steps import (
    general,
    simulation_time,
    influent,
    processes,
    connections,
    summary,
    save_section
)
from utils.input_helpers import ask_yes_no
from core.process.process_registry import ProcessRegistry

class CLIInterface:
    """
    Interface en ligne de commande interactive pour le simulateur
    """

    def __init__(self):
        """Initialise l'interface CLI"""
        registry = ProcessRegistry.get_instance()

        self.AVAILABLE_PROCESSES = registry.to_cli_format()
        self.DEFAULT_PARAMS = registry.to_default_params()
        
        self.config = {
            'name': '',
            'description': '',
            'simulation': {},
            'influent': {},
            'processes': []
        }

    def print_welcome(self):
        """Affiche le message de bienvenue"""
        print("\n" + "="*70)
        print(" "*8 + "CONFIGURATION INTERACTIVE DU SIMULATEUR DE PROCEDE")
        print("="*70)
        print("\nCe guide vous aidera à configurer votre simulation pas à pas.")
        print("Appuyez sur Entrée pour utiliser les valeurs par défaut [entre crochets].")
        print("="*70 + "\n")
        
    def run(self) -> Dict[str, Any]:
        """
        Lance l'interface interactive complète

        Returns:
            Dict[str, Any]: Configuration créée
        """
        self.print_welcome()

        # Etape 1 : Informations générales
        general.configure_general(self.config)

        # Etape 2 : Paramètres temporels
        simulation_time.configure_simulation_time(self.config)

        # Etape 3 : Influent
        influent.configure_influent(self.config)

        # Etape 4 : Sélection des procédés
        self.selected_process_keys = processes.select_processes(self.AVAILABLE_PROCESSES)

        # Etape 5 : Configuration de chaque procédés
        procs = processes.configure_processes(
            AVAILABLE_PROCESSES=self.AVAILABLE_PROCESSES,
            DEFAULT_PARAMS=self.DEFAULT_PARAMS,
            selected_keys=self.selected_process_keys
        )
        self.config['processes'].extend(procs)

        # Etape 6 : Configuration des connections
        connections.configure_connections(self.config)

        # Etape 7 : Récapitulatif
        summary.print_summary(self.config)

        # Etape 8 : Sauvegarde
        save = ask_yes_no("\nVoulez-vous sauvegarder cette configuration ?")
        if save:
            save_section.save_config(self.config)

        # Etape 9 : Lancement
        launch = ask_yes_no("\nVoulez vous lancer la simulation maintenant ?")
        self.config['_launch'] = bool(launch)

        return self.config
