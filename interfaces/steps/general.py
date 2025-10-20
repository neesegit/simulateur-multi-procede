from datetime import datetime
from typing import Dict
from utils import step

@step("ETAPE 1/7 : Informations générales")
def configure_general(config: Dict) -> None:
    """Configure les informations générales"""

    default_name = f"simulation_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    name = input(f"\nNom de la simulation [{default_name}] : ").strip() or default_name

    description = input("Description (optionnel) : ").strip() or "Simulation créée via CLI"

    config.update({
        "name": name,
        "description": description
    })

    print(f"\nSimulation créée : {config['name']}")