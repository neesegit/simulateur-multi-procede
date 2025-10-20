from typing import Dict, Any
from datetime import datetime
from utils import step

@step("ETAPE 6/7 : Récapitulatif")
def print_summary(config: Dict[str, Any]) -> None:
    print(f"\nNom : {config.get('name')}")
    print(f"Description : {config.get('description')}")

    sim = config.get('simulation',{})
    try:
        start = datetime.fromisoformat(sim['start_time'])
        end = datetime.fromisoformat(sim['end_time'])
        duration = (end - start).total_seconds()/3600
    except Exception:
        start = end = None
        duration = sim.get("total_hours", 0.0)

    if start and end:
        print("\nSimulation :")
        print(f"\tDébut : {start.strftime('%Y-%m-%d %H:%M')}")
        print(f"\tFin : {end.strftime('%Y-%m-%d %H:%M')}")
    else:
        print("\nSimulation : (dates invalides)")

    print(f"\tDurée : {duration:.1f}h")
    print(f"\tPas de temps : {sim['timestep_hours']}h")

    inf = config.get("influent", {})
    comp = inf.get("composition", {})
    print("\nInfluent")
    print(f"\tDébit : {inf.get('flowrate')} m^3/h")
    print(f"\tTempérature : {inf.get('temperature')}°C")
    print(f"\tDCO : {comp.get('cod')} mg/L")
    print(f"\tNH4 : {comp.get('nh4')} mg/L")

    procs = config.get("processes", [])
    print(f"\nChaîne de traitement ({len(procs)} procédé(s))")
    for i, p in enumerate(procs, 1):
        print(f"\t{i}. {p.get('name')} ({p.get('node_id')})")
        print(f"\t\tType : {p.get('type')}")
        print(f"\t\tVolume : {p.get('config', {}).get('volume', 'N/A')} m^3")