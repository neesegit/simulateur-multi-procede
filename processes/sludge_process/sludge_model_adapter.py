"""
Module qui permet d'adapter les différents modèles à une interface commune
"""
import numpy as np

from typing import Dict, Any, Optional
from models.asm1_model import ASM1Model

class SludgeModelAdapter:
    # TODO -> Registry des models comme pour les processes
    AVAILABLE = {
        'ASM1': ASM1Model,

    }

    def __init__(self, model_name: str, params: Optional[Dict[str, Any]] = None) -> None:
        if model_name not in self.AVAILABLE:
            raise ValueError(f"Modèle inconnu : {model_name}")
        self.name = model_name.upper()
        self.model = self.AVAILABLE[model_name](params=params or {})
        self.size = len(self.model.COMPONENT_INDICES)

    def dict_to_vector(self, data: Dict[str, float]) -> np.ndarray:
        return self.model.dict_to_concentrations(data)
    
    def vector_to_dict(self, vec: np.ndarray) -> Dict[str, float]:
        return self.model.concentrations_to_dict(vec)
    
    def reactions(self, c: np.ndarray) -> np.ndarray:
        return self.model.compute_derivatives(c)
    
    def enforce_oxygen_setpoint(self, c: np.ndarray, do_setpoint: float) -> None:
        idx = self.model.COMPONENT_INDICES.get('so')
        if idx is not None:
            c[idx] = do_setpoint

    def initial_state(self, do_setpoint: float) -> Dict[str, float]:
        if self.name == 'ASM1':
            return {
                'si': 30.0,
                'ss': 5.0, 
                'xi': 25.0, 
                'xs': 100.0,
                'xbh': 2500.0, 
                'xba': 150.0, 
                'xp': 450.0,
                'so': do_setpoint, 
                'sno': 5.0, 
                'snh': 2.0,
                'snd': 1.0, 
                'xnd': 5.0, 
                'salk': 7.0
            }
        return {}
