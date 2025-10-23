from dataclasses import dataclass
from typing import Dict, Any

@dataclass
class ProcessParameter:
    """Représente un paramètre de procédé"""
    name: str
    label: str
    unit: str
    default: float
    min: float
    max: float

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ProcessParameter':
        return cls(**data)