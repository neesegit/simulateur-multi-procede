from dataclasses import dataclass
from typing import Dict, Any

@dataclass
class ModelParameter:
    """Représente un paramètre de model"""
    id: str
    label: str
    unit: str
    default: float

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ModelParameter':
        return cls(**data)