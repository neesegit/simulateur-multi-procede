"""
DataBus et SimulationFlow pour la gestion des flux de données entre les différents procédés
"""
from typing import Dict, Any, List, Optional, Set
from dataclasses import dataclass, field
from datetime import datetime
import logging

@dataclass
class FlowData:
    """
    Représente les données d'un flux à un instant donné
    Structure flexible pour supporter différents modèles
    """
    timestamp: datetime
    flowrate: float # m^3/h
    temperature: float # °C

    # Paramètres tandards mesurables
    ss: float = 0.0 # Solides en suspension (mg/L)
    cod: float = 0.0 # DCO (mg/L)
    bod: float = 0.0 # DBO5 (mg/L)
    tkn: float = 0.0 # Azote Kjeldahl total (mg/L)

    # Tous les autres paramètres sont stockés dans un dict flexible
    components: Dict[str, float] = field(default_factory=dict)

    # Métadonnées
    source_node: Optional[str] = None
    model_type: Optional[str] = None # 'ASM1', etc

    def get(self, key: str, default: float = 0.0) -> float:
        """
        Récupère une valeur de composant

        Args :
            key : Nom du composant
            defautl : Valeur par défaut si non trouvé

        Returns :
            Valeur du composant
        """

        # Vérifie d'abord les attributs standards
        if hasattr(self, key) and key not in ['components', 'timestamp', 'source_node', 'model_type']:
            return getattr(self, key)
        return self.components.get(key, default)
    
    def set(self, key: str, value: float) -> None:
        """
        Définit une valeur de composant

        Args :
            key : Nom du composant
            value : Valeur à définir
        """

        if hasattr(self, key) and key not in ['components','timestamp','source_node','model_type']:
            setattr(self, key, value)
        else:
            self.components[key] = value
    
    def get_all_components(self) -> Dict[str, float]:
        """
        Retourne tous les composants (standards + spécifique au modèle)

        Returns:
            Dict[str, float]: Dictionnaire complet des composants
        """
        result = {
            'ss': self.ss,
            'cod': self.cod,
            'bod' : self.bod,
            'tkn' : self.tkn
        }
        result.update(self.components)
        return result
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convertit en dictionnaire

        Returns:
            Dict[str, Any]
        """

        return {
            'timestamp' : self.timestamp.isoformat(),
            'flowrate' : self.flowrate,
            'temperature' : self.temperature,
            'ss' : self.ss,
            'cod' : self.cod,
            'bod' : self.bod,
            'tkn' : self.tkn,
            'model_type' : self.model_type,
            'source_node' : self.source_node,
            'components' : self.components.copy()
        }
    
    def copy(self) -> 'FlowData':
        """
        Crée une copie du flux

        Returns:
            FlowData: Instance de FlowData
        """

        return FlowData(
            timestamp=self.timestamp,
            flowrate=self.flowrate,
            temperature=self.temperature,
            ss=self.ss,
            cod=self.cod,
            bod=self.bod,
            tkn=self.tkn,
            components=self.components.copy(),
            source_node=self.source_node,
            model_type=self.model_type
        )
    
    @classmethod
    def create_from_model(cls, 
                          timestamp: datetime,
                          flowrate: float,
                          temperature: float,
                          model_type: str,
                          auto_fractionate: bool = True,
                          **kwargs) -> 'FlowData':
        """
        Crée un FlowData pour un modèle spécifique

        Args:
            timestamp (datetime): Horodatage
            flowrate (float): Débit (m^3/h)
            temperature (float): Température (°C)
            model_type (str): Type de modèle ('ASM1', etc) 
            auto_fractionate (bool, optional): Si True, fractionne automatiquement les paramètres mesurés
            **kwargs: Valeurs des composants OU paramètres mesurés (DCO, MES, etc)

        Returns:
            FlowData: Instance de FlowData configurée
        """

        flow = cls(
            timestamp=timestamp,
            flowrate=flowrate,
            temperature=temperature,
            model_type=model_type
        )

        # Si fractionnement automatique demandé de DCO fournie
        if auto_fractionate and 'cod' in kwargs:
            from core.fraction import ASM1Fraction as fracasm1

            measured = {
                'cod_total': kwargs.pop('cod'),
                'ss': kwargs.pop('ss', 0.0),
                'tkn': kwargs.pop('tkn', 0.0),
                'nh4': kwargs.pop('nh4', 0.0),
                'no3': kwargs.pop('no3', 0.0),
                'po4': kwargs.pop('po4', 0.0),
            }

            for key in ['cod_soluble', 'no2', 'p_total', 'alkalinity', 'vfa_total', 'acetate', 'propionate']:
                if key in kwargs:
                    measured[key] = kwargs.pop(key)

            # Fractionne
            fractionated = fracasm1.fractionate(**measured)

            # Met à jour les composants avec les valeurs fractionnées
            flow.components.update(fractionated)

            # Garde les paramètres standards
            flow.cod = measured['cod_total']
            flow.ss = measured.get('ss', 0.0)
            flow.tkn = measured.get('tkn', 0.0)

        # Définit toutes les autres valeurs fournies
        for key, value in kwargs.items():
            flow.set(key, value)
        
        return flow
    
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
        Ecrit une donée dans le bus

        Args:
            key (str): Clé d'identification
            value (Any): Valeur à stocker
        """
        self._data_store[key] = value
        self.logger.debug(f"DataBus: Ecriture '{key}'")
    
    def read(self, key:str, default: Any = None) -> Any:
        """
        Lit une donée du bus

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
        if node_id not in self._history:
            self._history[node_id] = []
        self._history[node_id].append(flow_data)
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