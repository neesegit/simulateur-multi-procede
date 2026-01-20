import numpy as np
import logging

from typing import Literal, Any
from ode_solver import ODESolver
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass(frozen=True)
class SettlerContext:
    model: Any
    Q_in: float
    Q_underflow: float
    Q_overflow: float
    X_in: float
    area: float
    layer_height: float
    feed_layer: int

    X_min: float = 0.0
    X_max: float = 15000.0


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
            X (np.ndarray): Concnetrations actuelles par couche (mg/L)
            model: Modèle utilisé
            dt (float): Pas de temps (h)
            Q_in (float): Débit d'entrée (m^3/h)
            Q_underflow (float): Débit de soutirage (m^3/h)
            Q_overflow (float): Débit de surverse (m^3/h)
            X_in (float): TSS d'entrée (mg/L)
            area (float): Surface du décanteur (m²)
            layer_height (float): hauteur d'une couche (m)
            feed_layer (int): Index de la couche d'alimentation
            method (Literal['euler', 'rk4'], optional): Méthode numérique. Defaults to 'rk4'.
            X_min (float, optional): Concentration minimale autorisée. Defaults to 0.0.
            X_max (float, optional): Concentration maximale autorisée. Defaults to 15000.0.

        Returns:
            np.ndarray: Concentrations mises à jour
        """