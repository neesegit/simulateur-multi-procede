from dataclasses import dataclass
from typing import Any

@dataclass(frozen=True)
class SettlerContext:
    """
    Contexte opératoire pour un décanteur secondaire

    Attributs:
        model: Instance du modèle de sédimentation
        Q_in: Débit d'entrée (m^3/h)
        Q_underflow: Débit de soutirage (m^3/h)
        Q_overflow: Débit de surverse (m^3/h)
        X_in: Concentration de solides en entrée (mg/L)
        area: Surface du décanteur (m^2)
        layer_height: Hauteur d'une couche (m)
        feed_layer: Index de la couche d'alimentation
        X_min: Concentration minimale autorisée (mg/L)
        X_max: Concentration maximale autorisée (mg/L)
    """
    model: Any
    Q_in: float
    Q_underflow: float
    Q_overflow: float
    X_in: float
    area: float
    layer_height: float
    feed_layer: int
    X_min: float = 0.0
    X_max: float = 15000.0

    def to_dict(self) -> dict:
        """Convertit le contexte en dictionnaire pour les dérivées"""
        return {
            'Q_in': self.Q_in,
            'Q_underflow': self.Q_underflow,
            'Q_overflow': self.Q_overflow,
            'X_in': self.X_in,
            'area': self.area,
            'layer_height': self.layer_height,
            'feed_layer': self.feed_layer
        }
    
    def validate(self) -> bool:
        """Valide la cohérence du contexte"""
        if abs(self.Q_in - (self.Q_overflow + self.Q_underflow)) > 0.01:
            return False
        
        if self.Q_in <= 0 or self.Q_underflow <= 0 or self.Q_overflow <= 0:
            return False
        
        if self.area <= 0 or self.layer_height <= 0:
            return False
        
        if self.feed_layer < 0 or self.X_in < 0:
            return False
        
        return True