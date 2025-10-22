from typing import Dict, List, Any
from utils.decorators import step
from utils.input_helpers import ask_yes_no, ask_number

@step("ETAPE 6/8 : Configuration des connexions")
def configure_connections(config: Dict[str, Any]) -> None:
    """
    Configure les connexions entre procédés
    """
    processes = config.get('processes', [])
    if len(processes) == 0:
        print("\nAucun procédé à connecter")
        return
    if len(processes) == 1:
        print("\nUn seul procédé détecté. Il sera connecté directement à l'influent")
        config['connections'] = [
            {
                'source': 'influent',
                'target': processes[0]['node_id'],
                'fraction': 1.0,
                'is_recycle': False
            }
        ]
        return
    
    print("\n" + "="*70)
    print("Configuration des connexions entre procédés")
    print("="*70)

    print("\nProcédés disponibles :")
    for i, proc in enumerate(processes, 1):
        print(f"\t{i}. {proc['node_id']} - {proc['name']}")

    print("\nModes de connexion :")
    print("\t[1] Séquentiel simple : Influent -> P1 -> P2 -> ... -> sortie")
    print("\t[2] Avancé : configuration manuelle des connexions (recyclages, dérivations)")
    mode = input("\n Choisissez un mode [1] : ").strip() or "1"

    connections = []

    if mode == "1":
        connections = _create_sequential_connections(processes)
        print("\nChaîne séquentielle créée")
    else:
        connections = _create_advanced_connections(processes)

    config['connections'] = connections
    print("\n" + "="*70)
    print("Résumé des connexions :")
    print("="*70)
    for conn in connections:
        recycle_str = " (RECYCLAGE)" if conn.get('is_recycle') else ""
        fraction_str = f" [{conn.get('fraction', 1.0)*100:.0f}%]" if conn.get('fraction', 1.0) < 1.0 else ""
        print(f"  {conn['source']} → {conn['target']}{fraction_str}{recycle_str}")
    print("="*70)

def _create_sequential_connections(processes: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Crée une chaîne séquentielle simple"""
    connections = []
    connections.append({
        'source': 'influent',
        'target': processes[0]['node_id'],
        'fraction': 1.0,
        'is_recycle': False
    })

    for i in range(len(processes) - 1):
        connections.append({
            'source': processes[i]['node_id'],
            'target': processes[i+1]['node_id'],
            'fraction': 1.0,
            'is_recycle': False
        })
    return connections

def _create_advanced_connections(processes: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Configuration avancée des connexions"""
    connections = []
    proc_map = {str(i+1): proc['node_id'] for i, proc in enumerate(processes)}
    proc_map['0'] = 'influent'

    print("\n" + "="*70)
    print("Configuration manuelle des connexions")
    print("="*70)
    print("\nPour chaque connexion, indiquez :")
    print("\t- Source (0=influent, 1-N=procédés)")
    print("\t- Cible (1-N=procédés)")
    print("\t- Fraction du débit (0.0-1.0, défaut=1.0)")
    print("\t- Type (normal/recyclage)")
    print("\nTapez 'done' quand vous avez terminé\n")

    while True:
        print("\nProcédés disponibles :")
        print("\t[0] influent")
        for i, proc in enumerate(processes, 1):
            print(f"\t[{i}] {proc['node_id']} - {proc['name']}")

        source_input = input("\nSource [done pour terminer] : ").strip()
        if source_input.lower() == "done":
            break

        if source_input not in proc_map:
            print("Source invalide")
            continue

        source_id = proc_map[source_input]

        target_input = input("Cible : ").strip()
        if target_input not in proc_map or target_input == '0':
            print("Cible invalide")
            continue

        target_id = proc_map[target_input]

        if source_id == target_id:
            print("Source et cible doivent être différentes")
            continue

        fraction = ask_number(
            "Fraction du débit",
            default=1.0,
            min_val=0.01,
            max_val=1.0
        )

        is_recycle = ask_yes_no("Est-ce un recyclage ?", default=False)

        connections.append({
            'source': source_id,
            'target': target_id,
            'fraction': fraction,
            'is_recycle': is_recycle
        })

        print(f"Connexion ajoutée : {source_id} -> {target_id}")

    if not connections:
        print("\nAucune connexion définie, création d'une chaîne séquentielle")
        return _create_sequential_connections(processes)
    
    return connections
