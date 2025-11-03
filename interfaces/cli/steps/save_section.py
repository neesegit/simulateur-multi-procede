from typing import Dict, Any
from pathlib import Path
from interfaces import ConfigLoader
from utils.decorators import step

@step("ETAPE 8/8 — Sauvegarde de la configuration.")
def save_config(config: Dict[str, Any]) -> None:

    default_path = f"config/{config.get('name', 'simulation')}.json"
    path_input = input(f"\nChemin de sauvegarde [{default_path}]: ").strip()
    filepath = path_input if path_input else default_path

    Path(filepath).parent.mkdir(parents=True, exist_ok=True)

    # Retire les clés internes
    config_to_save = {k: v for k,v in config.items() if not k.startswith('_')}

    ConfigLoader.save(config_to_save, Path(filepath))
    print(f"\nConfiguration sauvegardée : {filepath}")