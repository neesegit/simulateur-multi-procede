"""
Ce module définit la classe de données Connection, qui représente une connexion entre deux noeuds
"""

from dataclasses import dataclass

@dataclass
class Connection:
    """
    Représente une connexion entre deux noeuds
    """

    source_id: str # ID du noeud source
    target_id: str # ID du noeud cible
    flow_fraction: float # Fraction du débit (0.0 à 1.0)
    is_recycle: bool # True si c'est un recyclage

    def __repr__(self):
        recycle_str = " (recycle)" if self.is_recycle else ""
        fraction_str = f" [{self.flow_fraction*100:.0f}%]" if self.flow_fraction <= 1.0 else ""
        return f"{self.source_id} => {self.target_id}{fraction_str}{recycle_str}"

