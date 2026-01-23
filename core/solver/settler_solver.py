import numpy as np
import logging

from typing import Literal
from core.solver.ode_solver import ODESolver
from core.context.settler_context import SettlerContext

logger = logging.getLogger(__name__)

class SettlerSolver:
    """
    Solveur temporel pour décanteur secondaire
    """

    @staticmethod
    def solve_step(
        X: np.ndarray,
        context: SettlerContext,
        dt: float,
        method: Literal['euler', 'rk4'] = 'rk4',
    ) -> np.ndarray:
        """
        Résout un pas de temps du décanteur

        Args:
            X (np.ndarray): Concentrations actuelles par couche (mg/L)
            context (SettlerContext): Contexte de simulation
            dt (float): Pas de temps (h)
            method (Literal[&#39;euler&#39;, 'rk4'], optional): Méthode numérique. Defaults to 'rk4'.

        Returns:
            np.ndarray: Concentrations mises à jour
        """
        if not context.validate():
            raise ValueError(
                "Contexte invalide: vérifier le bilan hydraulique et les paramètres"
            )
        
        def dX_dt(X_current: np.ndarray) -> np.ndarray:
            """Calcule dX/dt pour chaque couche"""
            X_clipped = np.clip(X_current, context.X_min, context.X_max)

            derivatives = context.model.derivatives(X_clipped, context.to_dict())

            return derivatives
        
        if method == 'euler':
            X_next = ODESolver.euler(X, dX_dt, dt)
        elif method == 'rk4':
            X_next = ODESolver.rk4(X, dX_dt, dt)
        else:
            raise ValueError(f"Méthode inconnue : {method}")
        
        X_next = np.clip(X_next, context.X_min, context.X_max)

        if np.any(np.isnan(X_next)) or np.any(np.isinf(X_next)):
            logger.warning(
                "Instabilité numérique détectée. "
                f"Réduction du pas de temps recommandée (dt={dt}h)"
            )
            return X
        return X_next
    
    @staticmethod
    def compute_effluent_quality(
        X: np.ndarray,
        context: SettlerContext
    ) -> dict:
        """
        Calcule la qualité de l'effluent

        Args:
            X (np.ndarray): Concentrations par couche
            conext (SettlerContext): Context du décanteur

        Returns:
            dict: Concentrations en sortie (overflow et underflow)
        """
        X_overflow = X[0]
        X_underflow = X[-1]

        mass_overflow = context.Q_overflow * X_overflow
        mass_underflow = context.Q_underflow * X_underflow

        return {
            'X_overflow': X_overflow,
            'X_underflow': X_underflow,
            'mass_overflow_kg_h': mass_overflow / 1000.0,
            'mass_underflow_kg_h': mass_underflow / 1000.0,
            'removal_efficiency': (1 - X_overflow / context.X_in) * 100 if context.X_in > 0 else 0
        }
    
    @staticmethod
    def detect_sludge_blanket(
        X: np.ndarray,
        threshold: float = 3000.0
    ) -> dict:
        """
        Détecte la position du voile de boues

        Args:
            X (np.ndarray): Concentrations par couche
            threshold (float, optional): Seuil de détection (mg/L). Defaults to 3000.0.

        Returns:
            dict: Informations sur le voile de boues
        """
        blanket_layers = np.where(X > threshold)[0]

        if len(blanket_layers) == 0:
            return {
                'has_blanket': False,
                'blanket_top_layer': None,
                'blanket_bottom_layer': None,
                'blanket_thickness_layers': 0
            }
        
        return {
            'has_blanket': True,
            'blanket_top_layer': int(blanket_layers[0]),
            'blanket_bottom_layer': int(blanket_layers[-1]),
            'blanket_thickness_layers': len(blanket_layers),
            'max_concentration': float(np.max(X))
        }