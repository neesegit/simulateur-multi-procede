from typing import Dict

from dataclasses import dataclass

@dataclass
class SteadyState:
    """Représente un état stationnaire calculé"""
    timestamp: str
    parameters: Dict[str, float]
    statistics: Dict[str, float]