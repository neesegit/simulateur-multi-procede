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

        self.COMPONENT_INDICES = {f'layer_{i}': i for i in range(self.n_layers)}

        logger.info(f"TakacsModel initialisé avec {self.n_layers} couches")

    @property
    def model_type(self) -> str:
        return "TakacsModel"
    
    def get_component_names(self) -> List[str]:
        """Retourn les noms des couches"""
        return [f'layer_{i}' for i in range(self.n_layers)]
    
    def get_component_label(self, layer_id: str) -> str:
        """Retourne un label descriptif pour une couche"""
        if not layer_id.startswith('layer_'):
            return layer_id
        
        try:
            layer_num = int(layer_id.split('_')[1])
            if layer_num == 0:
                return f"Couche {layer_num} (surface)"
            elif layer_num == self.n_layers - 1:
                return f"Couche {layer_num} (fond)"
            else:
                return f"Couche {layer_num}"
        except (IndexError, ValueError):
            return layer_id
    
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
            if x <= 0:
                vs[i] = v0
            else:
                term = exp_term[i]
                v_settling = v0 * (np.exp(-rh * term) - np.exp(-rp * term))
                vs[i] = max(0.0, min(v0, v_settling))
        
        return vs
    
    def compute_fluxes(self, state: np.ndarray, velocities: np.ndarray) -> np.ndarray:
        """
        Calcule les flux de solides entre les couches

        Args:
            state (np.ndarray): Concentrations par couche (mg/L)
            velocities (np.ndarray): Vitesses d'écoulement bulk par couche (m/h)

        Returns:
            np.ndarray: Flux entre couches (g/m²/h)
        """
        vs = self.compute_settling_velocity(state)

        J_total = velocities * state + vs * state

        return J_total
    
    def derivatives(self, state: np.ndarray, context: Optional[Dict] = None) -> np.ndarray:
        """
        Calcule dX/dt pour chaque couche selon le bilan de masse

        Pour la couche i:
        dX_i/dt = (J_{i-1} - J_i) / h_i + S_i

        où:
        - J_{i-1} = flux entrant de la couche supérieure
        - J_i = flux sortant vers la couche inférieure
        - h_i = hauteur de la couche
        - S_i = source/puits (alimentation)

        Args:
            state (np.ndarray): Vecteur d'état (concentrations par couche)
            context (Optional[Dict], optional): Contexte avec paramètres opératoires. Defaults to None.

        Returns:
            np.ndarray: Dérivées dX/dt
        """
        if context is None:
            raise ValueError("Le contexte est requis pour calculer les dérivées du settler")
        
        Q_in = context['Q_in']
        Q_underflow = context['Q_underflow']
        Q_overflow = context['Q_overflow']
        X_in = context['X_in']
        area = context['area']
        layer_height = context['layer_height']
        feed_layer = context['feed_layer']

        n = len(state)
        dXdt = np.zeros(n)

        v_bulk = np.zeros(n)

        for i in range(feed_layer):
            v_bulk[i] = Q_overflow / area

        for i in range(feed_layer + 1, n):
            v_bulk[i] = -Q_underflow / area

        v_bulk[feed_layer] = (Q_overflow - Q_in) / area

        fluxes = self.compute_fluxes(state, v_bulk)

        for i in range(n):
            if i == 0:
                J_in = 0
            else:
                J_in = fluxes[i-1]

            J_out = fluxes[i]

            if i == feed_layer:
                S_i = (Q_in / area) * X_in / layer_height
            else:
                S_i = 0
            
            dXdt[i] = (J_in - J_out) / layer_height + S_i

        return dXdt
    
    def dict_to_concentrations(self, state_dict: Dict[str, float]) -> np.ndarray:
        """Convertit un dictionnaire en vecteur de concentrations"""
        concentrations = np.zeros(self.n_layers)
        for name, value in state_dict.items():
            if name in self.COMPONENT_INDICES:
                concentrations[self.COMPONENT_INDICES[name]] = value
        return concentrations
    
    def concentrations_to_dict(self, state: np.ndarray) -> Dict[str, float]:
        """Convertit un vecteur de concentrations en dictionnaire"""
        return {name: state[idx] for name, idx in self.COMPONENT_INDICES.items()}