"""
DataBus et SimulationFlow pour la gestion des flux de données entre les différents procédés
"""
import logging

from typing import Dict, Any, Optional
from core.data.flow_data import FlowData

class DataBus:
    """
    Bus de données pour échanger des informations entre ProcessNodes
    """

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self._data_store: Dict[str, Any] = {}
        self._flow_store: Dict[str, FlowData] = {}

    def write(self, key: str, value: Any) -> None:
        """
        Ecrit une donnée dans le bus

        Args:
            key (str): Clé d'identification
            value (Any): Valeur à stocker
        """
        self._data_store[key] = value
        self.logger.debug(f"DataBus: Ecriture '{key}'")
    
    def read(self, key:str, default: Any = None) -> Any:
        """
        Lit une donnée du bus

        Args:
            key (str): Clé d'identification
            default (Any, optional): Valeur par défaut si la clé n'existe pas. Defaults to None.

        Returns:
            Any: Valeur associée à la clé ou default
        """
        value = self._data_store.get(key, default)
        return value
    
    def write_flow(self, node_id: str, flow_data: FlowData) -> None:
        """
        Ecrit les données d'un flux pour un noeud donné

        Args:
            node_id (str): ID du noeud source
            flow_data (FlowData): Données du flux
        """
        flow_data.source_node = node_id
        self._flow_store[node_id] = flow_data
        self.logger.debug(f"DataBus: Flux écrit pour noeud '{node_id}' (modèle: {flow_data.model_type})")

    def read_flow(self, node_id: str) -> Optional[FlowData]:
        """
        Lit les données de flux d'un noeud

        Args:
            node_id (str): ID du noeud source

        Returns:
            Optional[FlowData]: FlowData ou None si non trouvé
        """
        return self._flow_store.get(node_id)
    
    def clear(self) -> None:
        """
        Vide le bus de données
        """
        self._data_store.clear()
        self._flow_store.clear()
        self.logger.info("DataBus vidé")

    def get_all_flows(self) -> Dict[str, FlowData]:
        """
        Retourne tous les flux stockés

        Returns:
            Dict[str, FlowData]
        """
        return self._flow_store.copy()