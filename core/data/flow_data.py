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
    model_type: Optional[str] = None # 'ASM1', etc

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
    
    def get_all_components(self) -> Dict[str, float]:
        """
        Retourne tous les composants (standards + spécifique au modèle)

        Returns:
            Dict[str, float]: Dictionnaire complet des composants
        """
        return {**{k: getattr(self, k) for k in self._STANDARD_KEYS}, **self.components}
    
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

        flow = cls(timestamp, flowrate, temperature, model_type=model_type)

        # Si fractionnement automatique demandé de DCO fournie
        if auto_fractionate and 'cod' in kwargs:
            from core.fraction import ASM1Fraction as fracasm1

            measured = {k: kwargs.pop(k, 0.0) for k in ['cod', 'ss', 'tkn', 'nh4', 'no3', 'po4']}

            for key in ['cod_soluble', 'no2', 'p_total', 'alkalinity', 'vfa_total', 'acetate', 'propionate']:
                if key in kwargs:
                    measured[key] = kwargs.pop(key)

            # Fractionne
            fractionated = fracasm1.fractionate(**measured)

            # Met à jour les composants avec les valeurs fractionnées
            flow.components.update(fractionated)

            # Garde les paramètres standards
            for k in ['cod', 'ss', 'tkn']:
                setattr(flow, k , measured[k])

        # Définit toutes les autres valeurs fournies
        for key, value in kwargs.items():
            flow.set(key, value)
        
        return flow