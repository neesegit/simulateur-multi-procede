import numpy as np
import logging

from typing import Callable, Optional

logger = logging.getLogger(__name__)

class ODESolver:
    """
    Classe de base pour les solverus d'équations différentielles ordinaires
    """

    @staticmethod
    def euler(
        c: np.ndarray,
        dc_dt_func: Callable[[np.ndarray], np.ndarray],
        dt: float
    ) -> np.ndarray:
        """
        Méthode d'Euler explicite (simple, rapide, mais peut être instable)

        Args:
            c (np.ndarray): Vecteur de concentrations au temps t
            dc_dt_func (Callable[[np.ndarray], np.ndarray]): Fonction qui calcule dc/dt
            dt (float): Pas de temps

        Returns:
            np.ndarray: Vecteur de concentrations au temps t+dt
        """
        dc_dt = dc_dt_func(c)
        c_next = c + dc_dt * dt
        return np.maximum(c_next, 1e-10)
    
    @staticmethod
    def rk4(
        c: np.ndarray,
        dc_dt_func: Callable[[np.ndarray], np.ndarray],
        dt: float
    ) -> np.ndarray:
        """
        Méthode de Runge-Kutta d'ordre 4

        Args:
            c (np.ndarray): Vecteur de concentrations au temps t
            dc_dt_funct (Callable[[np.ndarray], np.ndarray]): Fonction qui calcule dc/dt
            dt (float): Pas de temps

        Returns:
            np.ndarray: Vecteur de concentrations au temps t+dt
        """
        k1 = dc_dt_func(c)

        c_k2= np.maximum(c + 0.5 * dt * k1, 1e-10)
        k2 = dc_dt_func(c_k2)

        c_k3 = np.maximum(c + 0.5 * dt * k2, 1e-10)
        k3 = dc_dt_func(c_k3)

        c_k4 = np.maximum(c + dt*k3, 1e-10)
        k4 = dc_dt_func(c_k4)

        c_next = c + (dt/6.0) * (k1 + 2*k2 + 2*k3 + k4)

        return np.maximum(c_next, 1e-10)
    