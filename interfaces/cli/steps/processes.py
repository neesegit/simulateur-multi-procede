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
                        DEFAULT_PARAMS: Dict[str, Dict[str, float]],
                        AVAILABLE_MODELS: Dict[str, Dict[str, Any]]) -> List[Dict[str, Any]]:
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
        config_params: Dict[str, Any] = {}
        defaults = DEFAULT_PARAMS.get(proc_type, {})

        # Choix du modèle si applicable
        selected_model = None
        if proc_info.get('has_model_choice'):
            selected_model_key = _select_model(AVAILABLE_MODELS)
            selected_model_type = AVAILABLE_MODELS[selected_model_key]['type']
            config_params['model'] = selected_model_type

        # Paramètres requis
        for param in proc_info['required_params']:
            if param == 'model':
                continue
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
                default_val = defaults.get(param)
                if isinstance(default_val, bool):
                    value = ask_yes_no(
                        f"\t{param.replace('_', ' ').title()}",
                        default=default_val
                    )
                elif isinstance(default_val, str) or default_val is None:
                    continue
                    display_default = default_val if default_val is not None else 'None'
                    value = input(f"\t{param.replace('_', ' ').title()} [{display_default}]: ").strip()
                    if not value:
                        value = default_val
                else:
                    value = ask_number(
                        f"\t{param.replace('_',' ').title()}",
                        default=default_val,
                        min_val=0
                    )
                config_params[param] = value
        else:
            # Utilise les valeurs par défaut
            for param in proc_info['optional_params']:
                if param == 'use_calibration':
                    config_params[param] = defaults.get(param, True)
                elif param == 'model_path':
                    config_params[param] = defaults.get(param, None)
                else:
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

def _select_model(AVAILABLE_MODELS: Dict[str, Dict[str, Any]]) -> str:
    """
    Permet de sélectionner un modèle

    Args:
        AVAILABLE_MODELS (Dict[str, Dict[str, Any]]): Dictionnaire des modèles disponibles

    Returns:
        str: Clé du modèle sélectionné
    """
    print("\nModèles disponibles :")
    for key, model in AVAILABLE_MODELS.items():
        print(f"\t[{key}] {model['name']}")
        print(f"\t\t{model['description']}")

    while True:
        choice = input("\nChoisissez un modèle [1] : ").strip() or "1"
        if choice in AVAILABLE_MODELS:
            selected = AVAILABLE_MODELS[choice]
            print(f"\nModèle sélectionné : {selected['name']}")
            return choice
        else:
            print("Choix invalide")