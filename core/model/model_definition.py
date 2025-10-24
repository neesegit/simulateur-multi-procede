import logging

from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional, Type
from importlib import import_module

from core.model.model_parameter import ModelParameter

logger = logging.getLogger(__name__)

@dataclass
class ModelDefinition:
    """Définition complète d'un model"""
    id: str
    type: str
    name: str
    description: str
    components_count: int
    processes_count: int
    default_temperature: float
    parameters: List[ModelParameter]
    components: List[Dict[str, str]]
    module: str
    class_name: str

    _class_cache: Optional[Type] = field(default=None, repr=False)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ModelDefinition':
        """Crée une ModelDefinition depuis un disctionnaire"""
        return cls(
            id=data['id'],
            type=data['type'],
            name=data['name'],
            description=data['description'],
            components_count=data['components_count'],
            processes_count=data['processes_count'],
            default_temperature=data['default_temperature'],
            parameters=[ModelParameter.from_dict(p) for p in data['parameters']],
            components=data.get('components', []),
            module=data['module'],
            class_name=data['class']
        )
    
    def get_class(self) -> Type:
        """Importe et retourne la classe du modèle"""
        if self._class_cache is None:
            try:
                module = import_module(self.module)
                self._class_cache = getattr(module, self.class_name)
                logger.debug(f"Classe modèle chargée : {self.module}.{self.class_name}")
            except (ImportError, AttributeError) as e:
                raise ImportError(
                    f"Impossible de charger {self.class_name} depuis {self.module} : {e}"
                )
        assert self._class_cache is not None
        return self._class_cache
    
    def get_param_dict(self) -> Dict[str, ModelParameter]:
        """Retourne les paramètres sous forme d'un dictionnaire"""
        return {p.id: p for p in self.parameters}
    def get_default_params(self) -> Dict[str, float]:
        """Retourne les valeurs par défaut des paramètres du modèle"""
        return {p.id: p.default for p in self.parameters}
    def get_components_names(self) -> List[str]:
        """Retourne la liste des noms de composants du modèle"""
        return [c.get('id', 'Inconnu') for c in self.components]
    
