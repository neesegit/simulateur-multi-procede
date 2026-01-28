from typing import Dict, List, Any, Optional
from utils.decorators import step
from utils.input_helpers import ask_number, ask_yes_no
from core.process.process_registry import ProcessRegistry

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
def configure_processes(
    selected_keys: List[str],
    AVAILABLE_PROCESSES: Dict[str, Dict[str, str]],
    DEFAULT_PARAMS: Dict[str, Dict[str, float]],
    AVAILABLE_MODELS: Dict[str, Dict[str, Any]]
) -> List[Dict[str, Any]]:
    """Configure chaque procédé sélectionné"""

    configured: List[Dict[str, Any]] = []
    registry = ProcessRegistry.get_instance()

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

        try:
            proc_definition = registry.get_process_definition(proc_type)
        except ValueError:
            print(f"Erreur : procédé {proc_type} non trouvé dans le registre")
            continue

        config_params = _configure_process_from_definition(
            proc_definition,
            AVAILABLE_MODELS if proc_info.get('has_model_choice') else None
        )

        process_config = {
            'node_id': node_id,
            'type': proc_type,
            'name': name,
            'config': config_params
        }

        configured.append(process_config)
        print(f"\n{name} configuré")

    return configured

def _configure_process_from_definition(
        proc_definition: Any,
        available_models: Optional[Dict[str, Dict[str, Any]]] = None
) -> Dict[str, Any]:
    """
    Configure un procédé à partir de sa définition

    Args:
        proc_definition (Any): Définition du procédé depuis le registre
        available_models (Optional[Dict[str, Dict[str, Any]]], optional): Modèles disponibles (si choix de modèle requis). Defaults to None.

    Returns:
        Dict[str, Any]: Configuration du procédé
    """
    config_params: Dict[str, Any] = {}

    if proc_definition.has_model_choice and available_models:
        selected_model_key = _select_model(available_models)
        selected_model_type = available_models[selected_model_key]['type']
        config_params['model'] = selected_model_type

    print("\nParamètres requis :")
    for param in proc_definition.required_params:
        if param.name == 'model' and 'model' in config_params:
            continue
        config_params[param.name] = _configure_parameter(param)

    advanced = ask_yes_no("\nConfigurer les paramètres avancés ?", default=False)
    if advanced:
        print("\nParamètres optionnels :")
        for param in proc_definition.optional_params:
            config_params[param.name] = _configure_parameter(param)
    
    return config_params

def _configure_parameter(param: Any) -> Any:
    """
    Configure un paramètre individuel en fonction de son type

    Args:
        param (Any): Objet ProcessParameter

    Returns:
        Any: Valeur configurée du paramètre
    """
    param_type = getattr(param, 'type', None)

    if param_type == 'choice':
        choices = getattr(param, 'choices', [])
        return _ask_choice(param.label, choices, param.default)
    
    elif param_type == 'boolean':
        return ask_yes_no(f"\t{param.label}", default=param.default)
    
    elif param_type == 'path':
        path = input(f"\t{param.label} [{param.default or 'None'}]: ").strip()
        return path if path else param.default
    
    else:
        min_val = getattr(param, 'min', None)
        max_val = getattr(param, 'max', None)

        need_int = 'layer' in param.name.lower() or 'count' in param.name.lower()
        value = ask_number(
            f"\t{param.label} ({param.unit})",
            default=param.default,
            min_val=min_val,
            max_val=max_val
        )
        return int(round(value)) if need_int else value

def _ask_choice(prompt: str, choices: List[str], default: str) -> str:
    """
    Demande à l'utilisateur de choisir parmi une liste

    Args:
        prompt (str): Message affiché
        choices (List[str]): Liste des choix possibles
        default (str): Valeur par défaut

    Returns:
        str: Choix sélectionné
    """
    print(f"\n{prompt} :")
    for i, choice in enumerate(choices, 1):
        marker = " (défaut)" if choice == default else ""
        print(f"\t[{i}] {choice}{marker}")

    while True:
        user_input = input(f"\nVotre choix [1-{len(choices)}]: ").strip()

        if not user_input:
            return default
        
        try:
            choice_idx = int(user_input) - 1
            if 0 <= choice_idx < len(choices):
                return choices[choice_idx]
            else:
                print(f"Choix invalide. Entrez un nombre entre 1 et {len(choices)}")
        except ValueError:
            print("Veuillez entrer un nombre valide")

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