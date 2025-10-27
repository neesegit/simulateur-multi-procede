from dataclasses import dataclass, field
from typing import Dict, Any, Optional, List

@dataclass
class ProcessParameter:
    """Représente un paramètre de procédé"""
    name: str
    label: str
    unit: str
    default: float
    min: Optional[float] = 0
    max: Optional[float] = 0

    type: Optional[str] = ""
    choices: Optional[List[str]] = field(default_factory=list)


    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ProcessParameter':
        return cls(**data)