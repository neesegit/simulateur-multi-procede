import numpy as np

from typing import Callable, Optional
from .ode_solver import ODESolver

class CSTRSolver:
    """
    Solveur spécialisé pour les réacteurs CSTR avec dilution
    """

    @staticmethod
    def solve_step(
        c: np.ndarray,
        c_in: np.ndarray,
        reaction_func: Callable[[np.ndarray], np.ndarray],
        dt: float,
        dilution_rate: float,
        method: str = 'rk4',
        oxygen_idx: Optional[int] = None,
        do_setpoint: Optional[float] = None
    ) -> np.ndarray:
        """
        Résout un pas de temps pour un CSTR

        Args:
            c (np.ndarray): Concentrations actuelles
            c_in (np.ndarray): Concentrations d'entrée
            reaction_func (Callable[[np.ndarray], np.ndarray]): Fonction de réactions biologiques
            dt (float): Pas de temps (jours)
            dilution_rate (float): Taux de dilution (1/j)
            method (str, optional): Méthode numérique ('euler', 'rk4'). Defaults to 'rk4'.
            oxygen_idx (Optional[int], optional): Index de l'oxygène dissous (pour contrôle). Defaults to None.
            do_setpoint (Optional[float], optional): Consigne d'oxygène. Defaults to None.

        Returns:
            np.ndarray: Nouvelles concentrations
        """
        def dc_dt_func(c_current: np.ndarray) -> np.ndarray:
            """Fonction combinée : dilution + réactions"""
            if oxygen_idx is not None and do_setpoint is not None:
                c_current = c_current.copy()
                c_current[oxygen_idx] = do_setpoint

            dilution_term = dilution_rate * (c_in - c_current)
            reaction_term = reaction_func(c_current)

            return dilution_term + reaction_term
        
        if method == 'euler':
            c_next = ODESolver.euler(c, dc_dt_func, dt)
        elif method == 'rk4':
            c_next = ODESolver.rk4(c, dc_dt_func, dt)
        else:
            raise ValueError(f"Méthode inconnue : {method}")
        
        if oxygen_idx is not None and do_setpoint is not None:
            c_next[oxygen_idx] = do_setpoint

        return c_next