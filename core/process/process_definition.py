import logging

from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional, Type
from importlib import import_module

from core.process.process_node import ProcessNode
from core.process.process_parameter import ProcessParameter

logger = logging.getLogger(__name__)

@dataclass
class ProcessDefinition:
    """Définition coplète d'un type de procédé"""
    id: str
    type: str
    name: str
    description: str
    category: str
    model: str
    required_params: List[ProcessParameter]
    optional_params: List[ProcessParameter]
    module: str
    class_name: str

    _class_cache : Optional[Type[ProcessNode]] = field(default=None, repr=False)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ProcessDefinition':
        """Crée une ProcessDefinition depuis un dictionnaire"""
        return cls(
            id=data['id'],
            type=data['type'],
            name=data['name'],
            description=data['description'],
            category=data['category'],
            model=data['model'],
            required_params=[ProcessParameter.from_dict(p) for p in data['required_params']],
            optional_params=[ProcessParameter.from_dict(p) for p in data['optional_params']],
            module=data['module'],
            class_name=data['class']
        )
    
    def get_class(self) -> Type[ProcessNode]:
        """
        Importe et retourne la classe du procédé

        Returns:
            Type[ProcessNode]: Utilise un cache pour éviter les imports multiples
        """
        if self._class_cache is None:
            try:
                module = import_module(self.module)
                self._class_cache = getattr(module, self.class_name)
                logger.debug(f"Classe chargée : {self.module}.{self.class_name}")
            except (ImportError, AttributeError) as e:
                raise ImportError(
                    f"Impossible de charger {self.class_name} depuis {self.module} : {e}"
                )
        assert self._class_cache is not None
        return self._class_cache
    
    def get_all_params(self) -> Dict[str, ProcessParameter]:
        """Retourne tous les paramètres (requis + optionnels)"""
        params = {}
        for p in self.required_params + self.optional_params:
            params[p.name] = p
        return params
    
    def get_default_config(self) -> Dict[str, float]:
        """Retourne une configuration avec les valeurs par défaut"""
        config = {}
        for param in self.required_params + self.optional_params:
            config[param.name] = param.default
        return config