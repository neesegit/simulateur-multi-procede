from typing import Dict, List, Any
from utils.decorators import step
from utils.input_helpers import ask_number, ask_yes_no

@step("ETAPE 4/8 : Sélection des procédés")
def select_processes(AVAILABLE_PROCESSES: Dict[str, Dict[str, str]]) -> List[str]:
    """Permet de sélectionner les procédés à simuler"""

    print("\nProcédés disponibles")
    for key, proc in AVAILABLE_PROCESSES.items():
        print(f"\t[{key}] {proc['name']}")
        print(f"\t\t{proc['description']}")

    selected: List[str] = []

    while True:
        print(f"\nProcédés séléctionnées : {len(selected)}")
        if selected:
            for i, proc_key in enumerate(selected, 1):
                proc = AVAILABLE_PROCESSES[proc_key]
                print(f"\t{i}. {proc['name']}")

        print("\nActions :")
        print("\t[numéro] - Ajouter un procédé")
        print("\t[d] - Supprimer le dernier")
        print("\t[ok] - Valider et continuer")

        choice = input("\nVotre choix : ").strip().lower()

        if choice == 'ok':
            if selected:
                break
            print("Vous devez sélectionner au moins un procédé")
        elif choice == 'd':
            if selected:
                removed = selected.pop()
                print(f"{AVAILABLE_PROCESSES[removed]['name']} retiré")
            else:
                print("Aucun procédé à retirer")
        elif choice in AVAILABLE_PROCESSES:
            selected.append(choice)
            print(f"{AVAILABLE_PROCESSES[choice]['name']} ajouté")
        else:
            print("Choix invalide")

    print(f"\n{len(selected)} procédé(s) sélectionné(s)")
    return selected
    

@step("ETAPE 5/8 : Configuration des procédés")
def configure_processes(selected_keys: List[str],
                        AVAILABLE_PROCESSES: Dict[str, Dict[str, str]],
                        DEFAULT_PARAMS: Dict[str, Dict[str, float]]) -> List[Dict[str, Any]]:
    """Configure chaque procédé sélectionné"""

    configured: List[Dict[str, Any]] = []

    for i, proc_key in enumerate(selected_keys, 1):
        proc_info = AVAILABLE_PROCESSES[proc_key]
        proc_type = proc_info['type']

        print("\n"+"="*70)
        print(f"Procédé {i}/{len(selected_keys)} : {proc_info['name']}")
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
        config_params: Dict[str, float] = {}
        defaults = DEFAULT_PARAMS.get(proc_type, {})

        # Paramètres requis
        for param in proc_info['required_params']:
            default_val = float(defaults.get(param, 0.0))
            value = ask_number(
                f"\t{param.replace('_',' ').title()}",
                default=default_val,
                min_val=0
            )
            config_params[param] = value

        # Paramètres optionnels
        advanced = ask_yes_no("\nConfigurer les paramètres avancés ? ", default=False)

        if advanced:
            for param in proc_info['optional_params']:
                default_val = float(defaults.get(param, 0.0))
                value = ask_number(
                    f"\t{param.replace('_',' ').title()}",
                    default=default_val,
                    min_val=0
                )
                config_params[param] = value
        else:
            # Utilise les valeurs par défaut
            for param in proc_info['optional_params']:
                config_params[param] = float(defaults.get(param, 0.0))

        # Ajoute le procédé à la config
        process_config = {
            'node_id': node_id,
            'type': proc_type,
            'name': name,
            'config': config_params
        }

        configured.append(process_config)
        print(f"\n{name} configuré")
    
    return configured