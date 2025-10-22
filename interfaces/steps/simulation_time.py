from datetime import datetime, timedelta
from typing import Dict
from utils.decorators import step
from utils.input_helpers import ask_number

@step("ETAPE 2/8 : Paramètres temporels")
def configure_simulation_time(config: Dict) -> None:
    """Configure les paramètres temporels"""

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
    duration_days = ask_number("   Jours", default=1, min_val=0)
    duration_hours = ask_number("   Heures", default=0, min_val=0, max_val=23)

    total_hours = duration_days*24+duration_hours
    end_time = start_time + timedelta(hours=total_hours) # pyright: ignore[reportOperatorIssue]

    # Pas de temps
    timestep = ask_number(
        "\nPas de temps (heures)",
        default=0.1,
        min_val=0.001,
        max_val=1.0
    )

    config.update({
        'simulation': {
            'start_time': start_time.isoformat(), # type: ignore
            'end_time': end_time.isoformat(),
            'timestep_hours': timestep
        }
    })

    total_steps = int(total_hours / timestep)
    print(f"\nPériode : {start_time.date()} -> {end_time.date()}") # pyright: ignore[reportAttributeAccessIssue]
    print(f"Pas de temps : {timestep}h ({total_steps} pas)")