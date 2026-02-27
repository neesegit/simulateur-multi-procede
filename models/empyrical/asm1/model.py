"""
Implémentation du modèle ASM1 (Activated Sludge Model 1)
Basé sur Henze et al. (2000)

Le modèle comprend :
- 13 composants (SI, SS, XI, XS, XBH, XBA, XP, SO, SNO, SNH, SND, XND, SALK)
- 8 processus biologiques
"""
import numpy as np
import logging

from typing import Dict, Optional

from core.model.model_registry import ModelRegistry
from models.empyrical.asm1.kinetics import calculate_process_rates
from models.empyrical.asm1.stoichiometry import build_stoichiometric_matrix

from models.reaction_model import ReactionModel

logger = logging.getLogger(__name__)

class ASM1Model(ReactionModel):
    """
    Modèle ASM1 pour la simulation des boues activées
    """

    def __init__(self, params: Optional[Dict[str, float]] = None):
        """
        Initialise le modèle ASM1

        Args:
            params (Dict[str, float], optional): Dictionnaire de paramètres. Utilise DEFAULT_PARAMS si None
        """
        super().__init__(params)

        registry = ModelRegistry.get_instance()
        model_definition = registry.get_model_definition('ASM1Model')
        self.DEFAULT_PARAMS = model_definition.get_default_params()

        self.COMPONENT_INDICES = {
            str(model_definition.get_components_names()[i]): i
            for i in range(len(model_definition.get_components_names()))
        }

        # Utilise les paramètres par défaut et override avec ceux fournis
        self.params = self.DEFAULT_PARAMS.copy()
        if params:
            self.params.update(params)

        # Construit la matrice stoechiométrique (8 processus x 13 composants)
        self._S = None

    @property
    def model_type(self) -> str:
        return "ASM1Model"
    
    def get_component_names(self) -> list:
        """
        Retourne les noms des 13 composants dans l'odre

        Returns:
            list
        """
        return list(self.COMPONENT_INDICES.keys())
    
    def process_rates(self, concentrations: np.ndarray) -> np.ndarray:
        """
        Calcule les vitesses des 8 processus biologiques

        Args:
            concentrations (np.ndarray): Vecteur des 13 concentrations

        Returns:
            np.ndarray: Vecteur des 8 vitesses de processus
        """
        return calculate_process_rates(concentrations, self.params)
    
    def stoichiometric_matrix(self) -> np.ndarray:
        """
        Construit la matrice soechiométrique S (8x13)

        Returns:
            np.ndarray: Matrice numpy 8x13
        """
        if self._S is None:
            self._S = build_stoichiometric_matrix(self.params)
        return self._S
    
    def concentrations_to_dict(self, state: np.ndarray) -> Dict[str, float]:
        """
        Convertit un vecteur de concentrations en dictionnaire

        Args:
            concentrations (np.ndarray): Vecteur numpy (13,)

        Returns:
            Dict[str, float]: Dictionnaire {nom_composant: valeur}
        """
        return {name: state[idx] for name, idx in self.COMPONENT_INDICES.items()}
    
    def dict_to_concentrations(self, state_dict: Dict[str, float]) -> np.ndarray:
        """
        convertit un dictionnaire de concentrations en vecteur numpy

        Args:
            conc_dict (Dict[str, float]): dictionnaire {nom_composant: valeur}

        Returns:
            np.ndarray: Vecteur numpy(13,)
        """
        concentrations = np.zeros(13)
        for name, value in state_dict.items():
            if name in self.COMPONENT_INDICES:
                concentrations[self.COMPONENT_INDICES[name]] = value
        return concentrations