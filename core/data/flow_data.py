from typing import Dict, Any, Optional
from dataclasses import dataclass, field, asdict
from datetime import datetime

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
    model_type: Optional[str] = None

    _STANDARD_KEYS = {'ss', 'cod', 'bod', 'tkn'}

    def get(self, key: str, default: float = 0.0) -> float:
        """
        Récupère une valeur de composant

        Args:
            key : Nom du composant
            default : Valeur par défaut si non trouvé

        Returns:
            Valeur du composant
        """

        # Vérifie d'abord les attributs standards
        if key in self._STANDARD_KEYS:
            return getattr(self, key, default)
        return self.components.get(key, default)
    
    def set(self, key: str, value: float) -> None:
        """
        Définit une valeur de composant

        Args:
            key : Nom du composant
            value : Valeur à définir
        """

        if key in self._STANDARD_KEYS:
            setattr(self, key, value)
        else:
            self.components[key] = value

    def has_model_components(self) -> bool:
        """Vérifie si le flux contient des composants de modèles"""
        return len(self.components) > 0
    
    def get_all_components(self) -> Dict[str, float]:
        """
        Retourne tous les composants (standards + spécifique au modèle)

        Returns:
            Dict[str, float]: Dictionnaire complet des composants
        """
        return {**{k: getattr(self, k) for k in self._STANDARD_KEYS}, **self.components}
    
    def extract_measured(self, keys: Optional[list[str]] = None) -> Dict[str, float]:
        if keys is None:
            keys = ['cod', 'ss', 'tkn', 'nh4', 'no3', 'po4', 'alkalinity']
        return {k: self.get(k, 0.0) for k in keys}
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convertit en dictionnaire

        Returns:
            Dict[str, Any]
        """
        data = asdict(self)
        data['timestamp'] = self.timestamp.isoformat()
        return data
    
    def copy(self) -> 'FlowData':
        """
        Crée une copie du flux

        Returns:
            FlowData: Instance de FlowData
        """
        return FlowData(**asdict(self))