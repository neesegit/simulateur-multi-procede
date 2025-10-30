"""
Module qui permet d'adapter les différents modèles à une interface commune
"""
import numpy as np
import logging

from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

class SludgeModelAdapter:
    """
    Adaptateur pour fournir une interface uniforme aux modèles biologiques
    """

    def __init__(self, model_instance: Any, model_name: str) -> None:
        self.name = model_name.upper()
        self.model = model_instance

        self.size = len(self.model.COMPONENT_INDICES)
        logger.debug(f"Adaptateur initialisé pour {self.name} ({self.size} composants)")

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
        elif self.name == 'ASM2D':
            return {
                'so2': do_setpoint,
                'sf': 10.0,
                'sa': 5.0,
                'snh4': 2.0,
                'sno3': 5.0,
                'spo4': 1.0,
                'si': 30.0,
                'salk': 5.0,
                'sn2': 0.0,
                'xi': 25.0,
                'xs': 100.0,
                'xh': 2000.0,
                'xpao': 300.0,
                'xpp': 90.0,
                'xpha': 20.0,
                'xaut': 100.0,
                'xtss': 2500.0,
                'xmeoh': 100.0,
                'xmep': 0.0
            }
        logger.warning(f"Pas d'état initial défini pour {self.name}")
        return {}
    
    def get_component_names(self) -> list:
        """Retourne la liste des noms de composants"""
        return self.model.get_component_names()
