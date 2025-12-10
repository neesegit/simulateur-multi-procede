"""
Méthode de calibration : résolution du steady-state par équations stationnaires
"""
import numpy as np
import logging

from abc import abstractmethod
from typing import Dict, Any, Optional, Tuple
from scipy.optimize import fsolve, least_squares
from datetime import datetime

from core.model.model_registry import ModelRegistry

from core.calibration.base_calibrator import BaseCalibrator
from core.calibration.calibration_result import CalibrationResult
from core.calibration.dataclass.calibration_metadata import CalibrationMetadata

logger = logging.getLogger(__name__)

class AnalyticalCalibrator(BaseCalibrator):
    """
    Calbrateur basé sur la résolution des équations stationnaires

    Principe : 
    Au steady-state, dC/dt = 0, donc :
    - Dilution + Réactions = 0
    - On résout ce système non linéaire
    """

    def __init__(
            self,
            process_id: str,
            process_config: Dict[str, Any],
            model_type: str,
            full_config: Optional[Dict[str, Any]],
            solver_method: str = 'hybr', # 'hybr', 'lm', 'trf'
            max_iterations: int = 1000,
            tolerance: float = 1e-6
    ):
        super().__init__(
            process_id=process_id,
            process_config=process_config,
            model_type=model_type,
            full_config=full_config,
            convergence_days=0,
            tolerance=tolerance
        )
        self.solver_method = solver_method
        self.max_iterations = max_iterations
        self.registry = ModelRegistry.get_instance()

        logger.info(
            f"Calibrateur analytique initialisé : {model_type} "
            f"(méthode={solver_method})"
        )

    def _run_calibration(self) -> Optional[CalibrationResult]:
        """Résout directement le système steady-state"""
        start_time = datetime.now()

        try:
            print("\n"+"-"*70)
            print("Résolution analytique de l'état stationnaire")
            print("-"*70)

            model_params = self.process_config.get('config', {}).get('model_parameters', {})
            model = self.registry.create_model(
                model_type=self.model_type,
                params=model_params
            )

            influent_config = self.full_config.get('influent', {}) if self.full_config else {}
            influent_components = self._prepare_influent(model, influent_config)

            volume = self.process_config.get('config', {}).get('volume', 5000.0)
            flowrate = influent_config.get('flowrate', 1000.0)
            dilution_rate = (flowrate / volume) * 24

            print(f"Volume du bassin : {volume:.1f} m^3")
            print(f"Débit d'entrée : {flowrate:.1f} m^3/h)")
            print(f"Taux de dilution : {dilution_rate:.3f} 1/j")
            print(f"HRT : {volume/flowrate:.2f}h")

            print("\nRésolution du système non-linéraire...")
            steady_state = self._solve_steady_state(
                model,
                influent_components,
                dilution_rate
            )

            if steady_state is None:
                print("Echec de la résolution")
                return None
            
            if not self._validate_solution(model, steady_state, influent_components, dilution_rate):
                print("Solution invalide (résidu trop élevés)")
                return None
            
            print("Solution trouvée et validée")

            elapsed = (datetime.now() - start_time).total_seconds()
            config_hash = self.comparator.compute_hash(self.process_config)

            metadata = CalibrationMetadata(
                process_id=self.process_id,
                model_type=self.model_type,
                config_hash=config_hash,
                created_at=datetime.now().isoformat(),
                calibration_time_hours=elapsed / 3600,
                converged=True,
                convergence_window=0,
                process_config=self.process_config
            )

            result = CalibrationResult(
                metadata=metadata,
                steady_states={self.process_id: steady_state},
                simulation_results={
                    'method': 'analytical',
                    'solver': self.solver_method,
                    'computation_time_seconds': elapsed
                }
            )

            self.cache.save(result)
            self.print_results(result)
            return result
        except Exception as e:
            logger.error(f"Erreur lors de la calibration analytique : {e}", exc_info=True)
            print(f"\nErreur : {e}")
            return None
    
    def _prepare_influent(self, model: Any, influent_config: Dict[str, Any]) -> np.ndarray:
        comp = influent_config.get('composition', {})

        if 'ASM1' in self.model_type.upper():
            from models.empyrical.asm1.fraction import ASM1Fraction as ModelFraction
        elif 'ASM2' in self.model_type.upper():
            from models.empyrical.asm2d.fraction import ASM2DFraction as ModelFraction
        elif 'ASM3' in self.model_type.upper():
            from models.empyrical.asm3.fraction import ASM3Fraction as ModelFraction
        else:
            raise ValueError(f"Modèle non supporté : {self.model_type}")
        
        fractionated = ModelFraction.fractionate(
            cod=comp.get('cod', 500),
            ss=comp.get('ss', 250),
            tkn=comp.get('tkn', 40),
            nh4=comp.get('nh4', 28),
            no3=comp.get('no3', 0.5),
            alkalinity=comp.get('alkalinity', 6.0)
        )
        return model.dict_to_concentrations(fractionated)
    
    def _solve_steady_state(
            self,
            model: Any,
            c_in: np.ndarray,
            dilution_rate: float
    ) -> Optional[Dict[str, float]]:
        """Résout le système dC/dt = 0"""
        def steady_state_equations(c: np.ndarray) -> np.ndarray:
            """
            Système d'équation à résoudre : F(C) = 0
            F(C) = D(C_in - C) + r(C)
            """
            c_copy = c.copy()
            if 'ASM1' in self.model_type:
                oxygen_idx = model.COMPONENT_INDICES.get('so', 7)
            else:
                oxygen_idx = model.COMPONENT_INDICES.get('so2', 0)

            do_setpoint = self.process_config.get('config', {}).get(
                'dissolved_oxygen_setpoint', 2.0
            )
            c_copy[oxygen_idx] = do_setpoint
            reactions = model.compute_derivatives(c_copy)
            dilution_term = dilution_rate * (c_in - c_copy)
            residuals = dilution_term + reactions

            residuals[oxygen_idx] = 0

            return residuals
        
        c0_from_cache = self._get_initial_guess_from_cache(model)

        if c0_from_cache is not None:
            c0 = c0_from_cache
            print("Estimation initiale chargée depuis le cache")
        else:
            c0 = self._compute_physical_initial_guess(model, c_in, dilution_rate)
            print("Estimation initiale calculée depuis des corrélations physiques")

        try:
            if self.solver_method == 'hybr':
                solution = fsolve(
                    steady_state_equations,
                    c0,
                    full_output=True,
                    xtol=self.tolerance
                )
                c_solution, info, ier, msg = solution

                if ier != 1:
                    print(f"Convergence partielle : {msg}")
                    return None
            else:
                result = least_squares(
                    steady_state_equations,
                    c0,
                    method=self.solver_method,
                    ftol=self.tolerance,
                    max_nfev=self.max_iterations,
                    verbose=1
                )       

                if not result.success:
                    print(f"Echec : {result.message}")
                    return None
                
                c_solution = result.x

            c_solution = np.maximum(c_solution, 1e-10)

            steady_state_dict = model.concentrations_to_dict(c_solution)

            return steady_state_dict
        except Exception as e:
            print(f"Erreur lors de la résolution : {e}")
            logger.error(f"Erreur solver : {e}", exc_info=True)
            return None
        
    def _get_initial_guess_from_cache(self, model: Any) -> Optional[np.ndarray]:
        """
        Récupère une estimation initiale depuis une calibration précédente
        """
        try:
            cached_result = self.cache.load(self.process_id, self.model_type, None)
            if cached_result and cached_result.steady_states:
                steady_state = list(cached_result.steady_states.values())[0]
                c0 = model.dict_to_concentrations(steady_state)
                logger.info("Estimation initiale chargée depuis cache")
                return c0
        except Exception as e:
            logger.debug(f"Pas de cache disponible : {e}")
        return None
    
    def _compute_physical_initial_guess(
            self,
            model: Any,
            c_in: np.ndarray,
            dilution_rate: float
    ) -> np.ndarray:
        """
        Calcule une estimation initiale basée sur des corrélations physiques
        """

        volume = self.process_config.get('config', {}).get('volume', 5000.0)
        flowrate = self.full_config.get('influent', {}).get('flowrate', 1000.0) if self.full_config else 1000.0

        hrt_hours = volume / flowrate
        hrt_days = hrt_hours / 24.0

        waste_ratio = self.process_config.get('config', {}).get('waste_ratio', 0.01)
        srt_days = 1.0 / (waste_ratio * dilution_rate) if waste_ratio > 0 else 10.0
        srt_days = np.clip(srt_days, 5.0, 30.0)

        print(f"\tHRT estimé : {hrt_hours:.2f} heures ({hrt_days:.2f} jours)")
        print(f"\tSRT estimé : {srt_days:.2f} jours")

        c0 = c_in.copy()

        substrate_reduction = 0.10

        c0 = self._physical_guess(model, c_in, hrt_days, srt_days, substrate_reduction)

        return c0
    
    @abstractmethod
    def _physical_guess(
            self,
            model: Any,
            c_in: np.ndarray,
            hrt_days: float,
            srt_days: float,
            substrate_reduction: float
    ) -> np.ndarray:
        """
        Estimation physique
        """
        pass

    def _validate_solution(
            self,
            model: Any,
            steady_state: Dict[str, float],
            c_in: np.ndarray,
            dilution_rate: float
    ) -> bool:
        """Vérifie que la solution satisfait bien dC/dt ~= 0"""
        c = model.dict_to_concentrations(steady_state)

        reactions = model.compute_derivatives(c)
        dilution_term = dilution_rate * (c_in - c)
        residuals = dilution_term + reactions

        if 'ASM1' in self.model_type:
            oxygen_idx = model.COMPONENT_INDICES.get('so', 7)
        else:
            oxygen_idx = model.COMPONENT_INDICES.get('so2', 0)
        residuals[oxygen_idx] = 0

        max_residual = np.max(np.abs(residuals))
        mean_concentrations = np.mean(np.abs(c))
        relative_error = max_residual / (mean_concentrations + 1e-10)

        print("\nValidation de la solution :")
        print(f"\tRésidu maximal : {max_residual:.2e}")
        print(f"\tErreur relative : {relative_error:.2e}")

        is_valid = relative_error < 0.01

        if not is_valid:
            print(f"Erreur trop élevée (seuil : 0.01) (error : {relative_error})")

        return is_valid