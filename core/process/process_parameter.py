from dataclasses import dataclass, field
from typing import Dict, Any, Optional, List, Union

@dataclass
class ProcessParameter:
    """Représente un paramètre de procédé"""
    name: str
    label: str
    unit: str
    default: Union[float, bool, str, None]
    min: Optional[float] = 0
    max: Optional[float] = 0
    type: Optional[str] = ""
    choices: Optional[List[str]] = field(default_factory=list)
    description: Optional[str] = None


    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ProcessParameter':
        return cls(
            name=data['name'],
            label=data['label'],
            unit=data.get('unit', ''),
            default=data.get('default'),
            min=data.get('min'),
            max=data.get('max'),
            type=data.get('type'),
            choices=data.get('choices', []),
            description=data.get('description')
        )
    
    def is_numeric(self) -> bool:
        """Vérifie si le paramètre est numérique"""
        return self.type in [None, 'number'] and isinstance(self.default, (int, float))
    
    def is_boolean(self) -> bool:
        """Vérifie si le paramètre est booléen"""
        return self.type == 'boolean' or isinstance(self.default, bool)
    
    def is_choice(self) -> bool:
        """Vérifie si le paramètre est un choix"""
        return self.type == 'choice' and len(self.choices or []) > 0
    
    def is_path(self) -> bool:
        """Vérifie si le paramètre est un chemin de fichier"""
        return self.type == 'path'