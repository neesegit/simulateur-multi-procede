import logging

from typing import Dict, Any, List, Optional
from core.data.flow_data import FlowData

class SimulationFlow:
    """
    Gère l'historique des flux durant une simulation
    Permet de tracer l'évolution temporelle des paramètres
    """

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self._history: Dict[str, List[FlowData]] = {}

    def add_flow(self, node_id: str, flow_data: FlowData) -> None:
        """
        Ajoute un point de données pour un noeud

        Args:
            node_id (str): ID du noeud
            flow_data (FlowData): Données à ajouter
        """
        self._history.setdefault(node_id, []).append(flow_data)
        self.logger.debug(f"SimulationFlow : Ajout pour '{node_id}' à {flow_data.timestamp}")

    def get_history(self, node_id: str) -> List[FlowData]:
        """
        Récupère l'historique d'un noeud

        Args:
            node_id (str): ID du noeud

        Returns:
            List[FlowData]: Liste chronologique des FlowData
        """
        return self._history.get(node_id, []).copy()
    
    def get_all_histories(self) -> Dict[str, List[FlowData]]:
        """
        Retourne tous les historiques

        Returns:
            Dict[str, List[FlowData]]
        """
        return {k: v.copy() for k, v in self._history.items()}
    
    def get_latest(self, node_id: str) -> Optional[FlowData]:
        """
        Récupère le dernier flux d'un noeud

        Args:
            node_id (str): ID du noeud

        Returns:
            Optional[FlowData]: Dernier FlowData ou None
        """
        history = self._history.get(node_id, [])
        return history[-1] if history else None
    
    def clear(self) -> None:
        """
        Vide l'historique
        """
        self._history.clear()
        self.logger.info("SimulationFlow vidé")

    def export_to_dict(self) -> Dict[str, List[Dict[str, Any]]]:
        """
        Exporte l'historique en dictonnaire sérialisable

        Returns:
            Dict[str, List[Dict[str, Any]]]: Dictionnaire avec les historiques sérialisés
        """
        return {
            node_id: [flow.to_dict() for flow in flows] for node_id, flows in self._history.items()
        }