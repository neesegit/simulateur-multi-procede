"""
Implémentation complète du modèle ASM3

Le modèle comprend :
- 13 composants
- 12 processus biologiques
"""
import numpy as np
import logging

from typing import Dict, Optional
from core.model.model_registry import ModelRegistry
from models.asm3.kinetics import calculate_process_rate
from models.asm3.stoichiometry import build_stoichiometric_matrix

logger = logging.getLogger(__name__)

class ASM3Model:
    """
    Modèle ASM3 pour la simulation des boues activées
    """

    def __init__(self, params: Optional[Dict[str, float]] = None) -> None:
        registry = ModelRegistry.get_instance()
        model_definition = registry.get_model_definition('ASM3Model')
        self.DEFAULT_PARAMS = model_definition.get_default_params()
        self.COMPONENT_INDICES = {
            model_definition.get_components_names()[i]: i
            for i in range(len(model_definition.get_components_names()))
        }

        self.params = self.DEFAULT_PARAMS.copy()
        if params:
            self.params.update(params)
        
        self.stoichiometric_matrix = build_stoichiometric_matrix(self.params)

    def compute_derivatives(self, c: np.ndarray) -> np.ndarray:
        rho = calculate_process_rate(c, self.params)
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
        concentration = np.zeros(13)
        for name, value in c_dict.items():
            if name in self.COMPONENT_INDICES:
                concentration[self.COMPONENT_INDICES[name]] = value
        return concentration