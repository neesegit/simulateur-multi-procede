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

        # Etape 1 : Informations générales
        self.configure_general()

        # Etape 2 : Paramètres temporels
        self.configure_simulation_time()

        # Etape 3 : Influent
        self.configure_influent()

        # Etape 4 : Sélection des procédés
        self.select_processes()

        # Etape 5 : Configuration de chaque procédés
        self.configure_processes()

        # Etape 6 : Récapitulatif
        self.print_summary()

        # Etape 7 : Sauvegarde
        save = self.ask_yes_no("\nVoulez-vous sauvegarder cette configuration ?")
        if save:
            filepath = self.save_config()
            print(f"\nConfiguration sauvegardée : {filepath}")

        # Etape 8 : Lancement
        launch = self.ask_yes_no("\nVoulez vous lancer la simulation maintenant ?")
        if launch:
            self.config['_launch'] = True

        return self.config

    def print_welcome(self):
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
                start_time = datetime.isoformat(start_input+"T00:00:00") # pyright: ignore[reportArgumentType]
            except:
                print("Format invalide, utilisation de la date par défaut")
                start_time = default_start
        else:
            start_time = default_start

        # Durée
        print("\nDurée de la simulation :")
        duration_days = self.ask_number("   Jours", default=1, min_val=0)
        duration_hours = self.ask_number("   Heures", default=0, min_val=0, max_val=23)

        total_hours = duration_days*24+duration_hours
        end_time = start_time + timedelta(hours=total_hours) # pyright: ignore[reportOperatorIssue]

        # Pas de temps
        timestep = self.ask_number(
            "\nPas de temps (heures)",
            default=0.1,
            min_val=0.001,
            max_val=1.0
        )

        self.config['simulation'] = {
            'start_time': start_time.isoformat(), # type: ignore
            'end_time': end_time.isoformat(),
            'timestep_hours': timestep
        }

        total_steps = int(total_hours / timestep)
        print(f"\nPériode : {start_time.date()} -> {end_time.date()}") # pyright: ignore[reportAttributeAccessIssue]
        print(f"Pas de temps : {timestep}h ({total_steps} pas)")

    def configure_influent(self):
        """Configure les caractéristiques de l'influent"""
        print("\n"+"-"*70)
        print("Etape 3/7 : Caractéristique de l'influent")
        print("-"*70)

        # Débit
        flowrate = self.ask_number(
            "\nDébit d'entrée (m^3/h)",
            default=1000.0,
            min_val=1.0
        )

        # Température
        temperature = self.ask_number(
            "Température (°C)",
            default=20.0,
            min_val=5.0,
            max_val=35.0
        )

        # Paramètres de pollution
        print("\nParamètres de pollution :")
        cod = self.ask_number("\tDCO totale (mg/L)", default=500.0, min_val=0)
        ss = self.ask_number("\tMES (mg/L)", default=250.0, min_val=0)
        tkn = self.ask_number("\tTKN - Azote Kjeldahl (mg/L)", default=40.0, min_val=0)
        nh4 = self.ask_number("\tNH4 - Ammonium (mg/L)", default=28.0, min_val=0)
        no3 = self.ask_number("\tNO3 - Nitrates (mg/L)", default=0.5, min_val=0)
        po4 = self.ask_number("\tPO4 - Phosphates (mg/L)", default=8.0, min_val=0)
        alkalinity = self.ask_number("\tAlcalinité (mmol/L)", default=6.0, min_val=0)

        self.config['influent'] = {
            'flowrate': flowrate,
            'temperature': temperature,
            'model_type': 'ASM1', # Pour l'instant fixé à ASM1
            'auto_fractionate': True,
            'composition': {
                'cod': cod,
                'ss': ss,
                'tkn': tkn,
                'nh4': nh4,
                'no3': no3,
                'po4': po4,
                'alkalinity': alkalinity
            }
        }

        print(f"\nInfluent configuré : Q = {flowrate} m^3/h, DCO = {cod} mg/L")

    def select_processes(self):
        """Permet de sélectionner les procédés à simuler"""
        print("\n"+"-"*70)
        print("Etape 4/7 : Sélection des procédés")
        print("-"*70)

        print("\nProcédés disponibles")
        for key, proc in self.AVAILABLE_PROCESSES.items():
            print(f"\t[{key}] {proc['name']}")
            print(f"\t\t{proc['description']}")

        selected = []

        while True:
            print(f"\nProcédés séléctionnées : {len(selected)}")
            if selected:
                for i, proc_key in enumerate(selected, 1):
                    proc = self.AVAILABLE_PROCESSES[proc_key]
                    print(f"\t{i}. {proc['name']}")

            print("\nActions :")
            print("\t[numéro] - Ajouter un procédé")
            print("\t[d] - Supprimer le dernier")
            print("\t[ok] - Valider et continuer")

            choice = input("\nVotre choix : ").strip().lower()

            if choice == 'ok':
                if selected:
                    break
                else:
                    print("Vous devez sélectionner au moins un procédé")
            elif choice == 'd':
                if selected:
                    removed = selected.pop()
                    print(f"{self.AVAILABLE_PROCESSES[removed]['name']} retiré")
                else:
                    print("Aucun procédé à retirer")
            elif choice in self.AVAILABLE_PROCESSES:
                selected.append(choice)
                print(f"{self.AVAILABLE_PROCESSES[choice]['name']} ajouté")
            else:
                print("Choix invalide")

        self.selected_process_keys = selected
        print(f"\n{len(selected)} procédé(s) sélectionné(s)")
    

    def configure_processes(self):
        """Configure chaque procédé sélectionné"""
        print("\n"+"-"*70)
        print("Etape 5/7 : Configuration des procédés")
        print("-"*70)

        for i, proc_key in enumerate(self.selected_process_keys, 1):
            proc_info = self.AVAILABLE_PROCESSES[proc_key]
            proc_type = proc_info['type']

            print("\n"+"="*70)
            print(f"Procédé {i}/{len(self.selected_process_keys)} : {proc_info['name']}")
            print("="*70)

            # ID et nom
            default_id = f"{proc_type.lower().replace('process','')}_{i}"
            node_id = input(f"\nIdentifiant unique [{default_id}]: ").strip()
            node_id = node_id if node_id else default_id

            default_name = f"{proc_info['name']} #{i}"
            name = input(f"Nom descriptif [{default_name}]: ").strip()
            name = name if name else default_name

            # Paramètres
            print("\nParamètres du procédé :")
            config = {}

            defaults = self.DEFAULT_PARAMS.get(proc_type, {})

            # Paramètres requis
            for param in proc_info['required_params']:
                default_val = defaults.get(param, 0.0)
                value = self.ask_number(
                    f"\t{param.replace('_',' ').title()}",
                    default=default_val,
                    min_val=0
                )
                config[param] = value

            # Paramètres optionnels
            advanced = self.ask_yes_no("\nConfigurer les paramètres avancés ? ", default=False)

            if advanced:
                for param in proc_info['optional_params']:
                    default_val = defaults.get(param, 0.0)
                    value = self.ask_number(
                        f"\t{param.replace('_',' ').title()}",
                        default=default_val,
                        min_val=0
                    )
                    config[param] = value
            else:
                # Utilise les valeurs par défaut
                for param in proc_info['optional_params']:
                    config[param] = defaults.get(param, 0.0)

            # Ajoute le procédé à la config
            process_config = {
                'node_id': node_id,
                'type': proc_type,
                'name': name,
                'config': config
            }

            self.config['processes'].append(process_config)

            print(f"\n{name} configuré")

    def print_summary(self):
        """Affiche un récapitulatif de la configuration"""
        print("\n"+"="*70)
        print("Etape 6/7 : Récapitulatif")
        print("="*70)

        print(f"\nNom : {self.config['name']}")
        print(f"Description : {self.config['description']}")

        sim = self.config['simulation']
        start = datetime.fromisoformat(sim['start_time'])
        end = datetime.fromisoformat(sim['end_time'])
        duration = (end - start).total_seconds()/3600
        print("\nSimulation :")
        print(f"\tDébut : {start.strftime('%Y-%m-%d %H:%M')}")
        print(f"\tFin : {end.strftime('%Y-%m-%d %H:%M')}")
        print(f"\tDurée : {duration:.1f}h")
        print(f"\tPas de temps : {sim['timestep_hours']}h")

        inf = self.config['influent']
        print("\nInfluent")
        print(f"\tDébit : {inf['flowrate']} m^3/h")
        print(f"\tTempérature : {inf['temperature']}°C")
        print(f"\tDCO : {inf['composition']['cod']} mg/L")
        print(f"\tNH4 : {inf['composition']['nh4']} mg/L")

        print(f"\nChaîne de traitement ({len(self.config['processes'])} procédé(s))")
        for i, proc in enumerate(self.config['processes'], 1):
            print(f"\t{i}. {proc['name']} ({proc['node_id']})")
            print(f"\t\tType : {proc['type']}")
            print(f"\t\tVolume : {proc['config'].get('volume', 'N/A')} m^3")

    def save_config(self) -> str:
        """
        sauvegarde la configuration

        Returns:
            str: Chemin du fichier sauvegardé
        """
        default_path = f"config/{self.config['name']}.json"
        path_input = input(f"\nChemin de sauvegarde [{default_path}]: ").strip()
        filepath = path_input if path_input else default_path

        Path(filepath).parent.mkdir(parents=True, exist_ok=True)

        # Retire les clés internes
        config_to_save = {k: v for k,v in self.config.items() if not k.startswith('_')}

        ConfigLoader.save(config_to_save, filepath)

        return filepath


# ============= Methode utilitaire ================
    def ask_number(self, prompt: str, default: float,
                   min_val: Optional[float] = None,
                   max_val: Optional[float] = None) -> float:
        """
        Demande un nombre à l'utilisateur avec validation

        Args:
            prompt (str): Message affiché
            default (float): Valeur par défaut
            min_val (Optional[float], optional): Valeur minimal autorisée. Defaults to None.
            max_val (Optional[float], optional): Valeur maximal autorisée. Defaults to None.

        Returns:
            float: Nombre saisi
        """
        while True:
            user_input = input(f"{prompt} [{default}]: ").strip()

            if not user_input:
                return default
            
            try:
                value = float(user_input)

                if min_val is not None and value < min_val:
                    print(f"Valeur trop petite (min : {min_val})")
                    continue

                if max_val is not None and value > max_val:
                    print(f"Valeur trop grande (max : {max_val})")
                    continue

                return value
            
            except ValueError:
                print(f"Veuillez entrer un nombre valide")

    def ask_yes_no(self, prompt: str, default: bool = True) -> bool:
        """
        Demande une confirmation oui/non

        Args:
            prompt (str): Message affiché
            default (bool, optional): Valeur par défaut. Defaults to True.

        Returns:
            bool: True si oui, False si non
        """
        default_str = "O/n" if default else "o/N"
        user_input = input(f"{prompt} [{default_str}]: ").strip().lower()

        if not user_input:
            return default
        
        return user_input in ['o', 'oui', 'y', 'yes']
    

    
        