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
from models.asm1.kinetics import calculate_process_rates
from models.asm1.stoichiometry import build_stoichiometric_matrix

logger = logging.getLogger(__name__)

class ASM1Model:
    """
    Modèle ASM1 pour la simulation des boues activées
    """

    def __init__(self, params: Optional[Dict[str, float]] = None):
        """
        Initialise le modèle ASM1

        Args:
            params (Dict[str, float], optional): Dictionnaire de paramètres. Utilise DEFAULT_PARAMS si None
        """

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
        self.stoichiometric_matrix = build_stoichiometric_matrix(self.params)
    
    
    def compute_derivatives(self, concentrations: np.ndarray) -> np.ndarray:
        """
        Calcule les dérivées dC/dt pour les 13 composants

        Explication :
        dC/dt = sum(vitesse_processus x coefficient_stoechiométrique)
        En algèbre matricielle : dC/dt = S^T x Rho

        Args:
            concentrations (np.ndarray): Vecteur des concentrations actuelles (13,)

        Returns:
            np.ndarray: Vecteur des dérivées dC/dt (13,)
        """
        # Calcule les vitesses des processus
        rho = calculate_process_rates(concentrations, self.params)

        # Multiplie par la matrice stoechiométrique transposée
        # S^T : 13x8, Rho : 8x1 -> résultat : 13x1
        derivatives = self.stoichiometric_matrix.T @ rho

        return derivatives
    
    def step(self, concentrations: np.ndarray, dt: float, so_setpoint: Optional[float] = None) -> np.ndarray:
        """
        Effectue un pas de temps de simulation avec méthode d'Euler

        Explication :
        Méthode d'Euler explicite : C(t+dt) = C(t) + dC/dt x dt

        C'est la méthode la plus simple pour résoudre une EDO
        Plus dt est petit, plus c'est précis

        Args:
            concentrations (np.ndarray): Concentrations au temps t (13,)
            dt (float): Pas de temps (jours)
            so_setpoint (float, optional): Consigne d'oxygène dissous(mg/L) - si fournie, SO est fixé

        Returns:
            np.ndarray: Concentrations au temps t+dt (13,)
        """
        # Calcule les dérivées
        derivatives = self.compute_derivatives(concentrations)

        # Méthode d'Euler : C_next = C_current + dC/dt x dt
        concentration_next = concentrations + derivatives*dt

        # Contraintes : concentration >= 0 (pas de valeurs négatives)
        concentrations_next = np.maximum(concentration_next, 1e-10)

        # Si consigne d'oxygène fournie, on la fixe (contrôle d'aération)
        if so_setpoint is not None:
            concentrations_next[7] = so_setpoint

        return concentrations_next
    
    def get_component_names(self) -> list:
        """
        Retourne les noms des 13 composants dans l'odre

        Returns:
            list
        """
        return list(self.COMPONENT_INDICES.keys())
    
    def concentrations_to_dict(self, concentrations: np.ndarray) -> Dict[str, float]:
        """
        Convertit un vecteur de concentrations en dictionnaire

        Args:
            concentrations (np.ndarray): Vecteur numpy (13,)

        Returns:
            Dict[str, float]: Dictionnaire {nom_composant: valeur}
        """
        return {name: concentrations[idx] for name, idx in self.COMPONENT_INDICES.items()}
    
    def dict_to_concentrations(self, conc_dict: Dict[str, float]) -> np.ndarray:
        """
        convertit un dictionnaire de concentrations en vecteur numpy

        Args:
            conc_dict (Dict[str, float]): dictionnaire {nom_composant: valeur}

        Returns:
            np.ndarray: Vecteur numpy(13,)
        """
        concentrations = np.zeros(13)
        for name, value in conc_dict.items():
            if name in self.COMPONENT_INDICES:
                concentrations[self.COMPONENT_INDICES[name]] = value
        return concentrations