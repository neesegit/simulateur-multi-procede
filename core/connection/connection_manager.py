"""
Ce module définit la classe ConnectionManager, responsable de la gestion complètre du graphe de connexions entre noeuds

Elle s'appuie sur la dataclass Connection pour représenter chaque lien
"""
import logging

from typing import List, Set, Tuple, Dict, Any
from .connection import Connection

logger = logging.getLogger(__name__)

class ConnectionManager:
    """
    Gère le graphe complet de connexions
    """

    _connections: List[Connection]
    _nodes: Set[str]

    def __init__(self):
        self._connections = []
        self._nodes = set()

    def add_connection(self, 
                       source_id: str, 
                       target_id: str, 
                       flow_fraction: float = 1.0, 
                       is_recycle: bool = False) -> None:
        """
        Ajoute une connexion au graphe

        Args:
            source_id (str): ID du noeud source
            target_id (str): ID du noeud cible
            flow_fraction (float, optional): Fraction du débit (0 < fraction <= 1.0). Defaults to 1.0.
            is_recycle (bool, optional): True si c'est un recyclage. Defaults to False.

        Raises:
            ValueError si flow_fraction invalide
        """

        if flow_fraction <= 0 or flow_fraction > 1.0:
            raise ValueError(f"flow_fraction doit être dans ]0, 1], reçu : {flow_fraction}")
        if source_id == target_id:
            raise ValueError("source_id et target_id doivent être différents")
        
        conn = Connection(source_id, target_id, flow_fraction, is_recycle)

        self._connections.append(conn)
        self._nodes.add(source_id)
        self._nodes.add(target_id)

        logger.debug(f"Connexion ajoutée : {conn}")

    def get_upstream_nodes(self, node_id: str) -> List[Tuple[str, Connection]]:
        """
        Trouve tous les noeuds qui envoient du flux vers node_id

        Args:
            node_id (str): ID du noeud

        Returns:
            List[Tuple[str, Connection]]: Liste de tuples (source_id, Connection)
        """
        upstream = []

        for conn in self._connections:
            if conn.target_id == node_id:
                upstream.append((conn.source_id, conn))
        
        return upstream
    
    def get_downstream_nodes(self, node_id: str) -> List[Tuple[str, Connection]]:
        """
        Trouve tous les noeuds qui reçoivent du flux depuis node_id

        Args:
            node_id (str): ID du noeud

        Returns:
            List[Tuple[str, Connection]]: Liste de tuples (target_id, Connection)
        """
        downstream = []

        for conn in self._connections:
            if conn.source_id == node_id:
                downstream.append((conn.target_id, conn))
        return downstream
    
    def get_execution_order(self) -> List[str]:
        """
        Calcule l'ordre d'exécution des noeuds

        Algorithme: Tri topologique (Kahn's algorithm)

        Principe:
        1. Ignorer les recyclages (sinon boucle infinie)
        2. Trouver les noeuds sans dépendances
        3. Les traiter et retirer du graphe
        4. Répéter jusqu'a avoir traité tous les noeuds

        Returns:
            List[str]: Liste de node_id dans l'ordre d'exécution
        
        Raises:
            ValueError si cycle détecté (hors recyclage)
        """
        non_recycle_edges = {}
        in_degree = {node: 0 for node in self._nodes}

        for conn in self._connections:
            if not conn.is_recycle:
                if conn.source_id not in non_recycle_edges:
                    non_recycle_edges[conn.source_id] = []

                non_recycle_edges[conn.source_id].append(conn.target_id)

                in_degree[conn.target_id] += 1
        
        queue = [node for node, degree in in_degree.items() if degree == 0]

        order = []

        while not queue:
            current = queue.pop(0)
            order.append(current)

            for neighbor in non_recycle_edges.get(current, []):
                in_degree[neighbor] -= 1
                queue.append(neighbor)

        if len(order) != len(self._nodes):
            raise ValueError("Cycle détecté dans le graphe (hors recyclage)."
                             "Marquez les recyclages avec is_recycle=True")
        
        logger.info(f"Ordre d'exécution calculé : {'->'.join(order)}")
        return order
    
    def detect_cycles(self) -> List[List[str]]:
        """
        Détecte tous lescycles dans le graphe complet (avec recyclages)

        Algorithme : DFS (Depth-First search)
        
        Returns:
            List[List[str]]: Liste des cycles détectés (chaque cycle = liste de node_id)
        """
        def dfs(node: str, visited: Set[str], rec_stack: Set[str], path: List[str]) -> List[str]|None:
            visited.add(node)
            rec_stack.add(node)
            path.append(node)

            for target_id, _ in self.get_downstream_nodes(node):
                if target_id not in visited:
                    # Explorer plus loin
                    cycle = dfs(target_id, visited, rec_stack, path.copy())
                    if cycle:
                        return cycle
                    
                elif target_id in rec_stack:
                    # On est tombé sur un noeud déjà dans la pile -> cycle
                    cycle_start = path.index(target_id)
                    return path[cycle_start:] + [target_id]
            
            rec_stack.remove(node)
            return None
        
        cycles = []
        visited = set()

        for node in self._nodes:
            if node not in visited:
                cycle = dfs(node,visited, set(), [])
                if cycle and cycle not in cycles:
                    cycles.append(cycle)
        return cycles
    
    def validate(self) -> Dict[str, Any]:
        """
        Valide la cohérence du graphe

        Returns:
            Dict[str, Any]: Dictionnaire des erreurs et des warnings
        """
        validation = {
            'errors': [],
            'warnings': []
        }
        for node in self._nodes:
            downstream = self.get_downstream_nodes(node)

            non_recycle_downstream = [
                conn for _, conn in downstream
                if not conn.is_recycle
            ]

            if non_recycle_downstream:
                total_fraction = sum(
                    conn.flow_fraction
                    for conn in non_recycle_downstream
                )

                if total_fraction > 1.01:
                    validation['errors'].append(
                        f"Node '{node}' : somme des fractions = {total_fraction:.2f} > 1.0"
                    )
        
        cycles = self.detect_cycles()

        for cycle in cycles:
            cycle_connection = [
                conn for conn in self._connections
                if conn.source_id in cycle and conn.target_id in cycle
            ]

            if all(not conn.is_recycle for conn in cycle_connection):
                validation['warnings'].append(
                    f"Cycle détecté sans recyclage marqué : {'->'.join(cycle)}"
                )

        for node in self._nodes:
            upstream = self.get_upstream_nodes(node)
            downstream = self.get_downstream_nodes(node)

            if not upstream and not downstream:
                validation['warnings'].append(
                    f"Noeud isolé (aucune connexion) : '{node}'"
                )

        return validation

    def to_dict(self) -> Dict[str, Any]:
        return {
            'nodes': list(self._nodes),
            'connections' : [
                {
                    'source': conn.source_id,
                    'target': conn.target_id,
                    'fraction': conn.flow_fraction,
                    'is_recycle': conn.is_recycle
                }
                for conn in self._connections
            ]
        }
    
    def visualize_ascii(self) -> str:
        """
        Génère une représentation ASCII du graphe

        Returns:
            str: String multi-lignes représentant le graphe
        """
        lines = ["Graphe de connexions : ", "="*50]

        for node in sorted(self._nodes):
            downstream = self.get_downstream_nodes(node)

            if downstream:
                for target_id, conn in downstream:
                    # Fraction (si < 100%)
                    fraction_str = (
                        f" [{conn.flow_fraction*100:.0f}%]"
                        if conn.flow_fraction < 1.0
                        else ""
                    )

                    recycle_str = " (recycle)" if conn.is_recycle else ""

                    lines.append(
                        f" {node} -> {target_id}{fraction_str}{recycle_str}"
                    )
            else:
                lines.append(f" {node} (sortie)")
        lines.append("="*50)

        return "\n".join(lines)
    
    def __repr__(self) -> str:
        return (
            f"<ConnectionManager("
            f"nodes={len(self._nodes)}, "
            f"connections={len(self._connections)}>"
        )


