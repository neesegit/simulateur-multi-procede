from typing import Optional



def ask_number(prompt: str, default: float,
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

def ask_yes_no(prompt: str, default: bool = True) -> bool:
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