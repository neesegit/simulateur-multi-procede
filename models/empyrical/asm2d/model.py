"""
Implémentation complète du modèle ASM2d

Le modèle comprend :
- 19 composants
- 21 processus biologiques
- 45 paramètres cinétiques et stoechiométriques
"""
import numpy as np
import logging

from typing import Dict, Optional
from core.model.model_registry import ModelRegistry
from models.empyrical.asm2d.kinetics import calculate_process_rates
from models.empyrical.asm2d.stoichiometry import build_stoichiometric_matrix

from models.empyrical_model import EmpyricalModel

logger = logging.getLogger(__name__)

class ASM2dModel(EmpyricalModel):
    """
    Modèle ASM2d pour la simulation des boues activées avec déphosphatation biologique
    """

    def __init__(self, params: Optional[Dict[str, float]] = None) -> None:
        registry = ModelRegistry.get_instance()
        model_definition = registry.get_model_definition('ASM2dModel')
        self.DEFAULT_PARAMS = model_definition.get_default_params()
        self.COMPONENT_INDICES = {
            model_definition.get_components_names()[i]: i
            for i in range(len(model_definition.get_components_names()))
        }

        self.params = self.DEFAULT_PARAMS.copy()
        if params:
            self.params.update(params)

        self.stoichiometric_matrix = build_stoichiometric_matrix(self.params)

    def compute_derivatives(self, concentrations: np.ndarray) -> np.ndarray:
        rho = calculate_process_rates(concentrations, self.params)
        derivatives = self.stoichiometric_matrix.T @ rho
        return derivatives
    
    def get_component_names(self) -> list:
        """
        Retourne les noms des composants dans l'ordre

        Returns:
            list
        """
        return list(self.COMPONENT_INDICES.keys())
    
    def concentrations_to_dict(self, c: np.ndarray) -> Dict[str, float]:
        """Convertit un vecteur de concentrations en dictionnaire

        Args:
            c (np.ndarray): Concentration, vecteur numpy

        Returns:
            Dict[str, float]: Dictionnaire {nom_composant: valeur}
        """
        return {name: c[idx] for name, idx in self.COMPONENT_INDICES.items()}
    
    def dict_to_concentrations(self, c_dict: Dict[str, float]) -> np.ndarray:
        """
        Convertit un dictionnaire de concentrations en vecteur numpy

        Args:
            c_dict (Dict[str, float]): Dictionnaire {nim_composant: valeur}

        Returns:
            np.ndarray: Vecteur numpy
        """
        concentration = np.zeros(19)
        for name, value in c_dict.items():
            if name in self.COMPONENT_INDICES:
                concentration[self.COMPONENT_INDICES[name]] = value
        return concentration
        