"""Implémentation du modèle de Takacs pour la décantation secondaire"""
import numpy as np
import logging

from typing import Dict, Optional, List
from core.model.model_registry import ModelRegistry
from models.transport_model import TransportModel

logger = logging.getLogger(__name__)

class TakacsModel(TransportModel):
    """
    Modèle de Takacs pour la sédimentation et l'épaississement des boues

    Le modèle divise le clarificateur en couches et calcule:
    - La vitesse de sédimentation en fonction de la concentration
    - Les flux de solides entre couches
    - La formation de voile de boues
    """

    def __init__(self, params: Optional[Dict[str, float]] = None):
        """
        Initialise le modèle de Takacs

        Args:
            params (Optional[Dict[str, float]], optional): Paramètres du modèle. Defaults to None.
        """
        super().__init__(params)

        registry = ModelRegistry.get_instance()
        model_definition = registry.get_model_definition('TakacsModel')
        self.DEFAULT_PARAMS = model_definition.get_default_params()

        if params:
            self.params.update(params)
        else:
            self.params = self.DEFAULT_PARAMS.copy()

        self.n_layers = int(self.params.get('n_layers', 10))

        self.Q_in = 0.0
        self.Q_underflow = 0.0
        self.Q_overflow = 0.0
        self.X_in = 0.0
        self.feed_layer = 5
        self.area = 1000.0
        self.layer_height = 0.4

        logger.info(f"TakacsModel initialisé avec {self.n_layers} couches")

    @property
    def model_type(self) -> str:
        return "TakacsModel"
    
    def compute_settling_velocity(self, X: np.ndarray) -> np.ndarray:
        """
        Calcule la vitesse de sédimentation selon le modèle de Takacs

        vs(X) = max(0, min(v0, v0*(exp(-rh*(X-fns*X_f)) - exp(-rp*(X-fns*X_f))))) 

        Args:
            X (np.ndarray): Concentrations de solides dans chaque couche

        Returns:
            np.ndarray: Vitesses de sédimentation
        """
        v0 = self.params['v0']
        rh = self.params['rh']
        rp = self.params['rp']
        fns = self.params['fns']
        X_f = self.params['x_f']

        exp_term = X - fns * X_f

        vs = np.zeros_like(X)
        for i, x in enumerate(X):
            term = exp_term[i]
            v_settling = v0 * (np.exp(-rh * term) - np.exp(-rp * term))
            vs[i] = max(0.0, min(v0, v_settling))
        
        return vs
    
    def compute_flux(
            self,
            X: np.ndarray,
            vs: np.ndarray,
            v_bulk: float
    ) -> np.ndarray:
        """
        Calcule le flux de solides dans chaque couche

        J = v_bulk * X + vs * X (flux gravitaire + flux convectif)

        Args:
            X (np.ndarray): Concentrations (mg/l)
            vs (np.ndarray): Vitesses de sédimentation (m/h)
            v_bulk (float): Vitesse d'écoulement du liquide (m/h)

        Returns:
            np.ndarray: Flux de solides (g/m²/h)
        """
        J_conv = v_bulk * X
        J_grav = vs * X
        J_total = J_conv + J_grav
        return J_total

    def compute_fluxes(self, state: np.ndarray, velocities: np.ndarray) -> np.ndarray:
        