import logging
import numpy as np

from typing import Dict, Any, Optional, Tuple, List
from abc import ABC, abstractmethod
from datetime import datetime, timedelta

from .calibration_cache import CalibrationCache
from .configuration_comparator import ConfigurationComparator
from .calibration_result import CalibrationResult

from core.orchestrator.simulation_orchestrator import SimulationOrchestrator

from utils.input_helpers import ask_yes_no

class BaseCalibrator(ABC):
    """
    Classe abstraite pour tous les calibrateurs

    Définit l'interface générale et la logique commune
    """

    def __init__(
        self,
        process_id: str,
        process_config: Dict[str, Any],
        model_type: str,
        full_config: Optional[Dict[str, Any]] = None,
        convergence_days: float = 200.0,
        tolerance: float = 0.01,
        check_interval: int = 50,
        convergence_window: int = 100
    ) -> None:
        """
        Initialise le calibrateur

        Args:
            process_id (str): ID unique du procédé
            process_config (Dict[str, Any]): Configuration du procédé
            model_type (str): Type du modèle
            full_config (Dict[str, Any], optional): Configuration complète (incluant influent). Defaults to None
            convergence_days (float, optional): Durée maximale de calibration. Defaults to 200.0.
            tolerance (float, optional): Tolérance de convergence (%). Defaults to 0.01.
            check_interval (int, optional): Vérification tous les N pas. Defaults to 50.
            convergence_window (int, optional): Fenêtre pour vérifier la convergence. Defaults to 100.
        """
        self.process_id = process_id
        self.process_config = process_config
        self.model_type = model_type
        self.full_config = full_config

        self.convergence_days = convergence_days
        self.tolerance = tolerance
        self.check_interval = check_interval
        self.convergence_window = convergence_window

        self.cache = CalibrationCache()
        self.comparator = ConfigurationComparator()

        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")

        self.logger.info(
            f"Calibrateur initialisé : {self.__class__.__name__} "
            f"pour {model_type} ({process_id})"
        )

    @abstractmethod
    def get_convergence_parameters(self) -> List[str]:
        """
        Retourne la lsite des paramètres à vérifier pour la convergence

        Returns:
            List[str]: Noms des paramètres
        """
        pass

    @abstractmethod
    def get_key_output_parameters(self) -> List[str]:
        """
        Retourne les paramètres clés à extraire

        Returns:
            List[str]: Noms des paramètres de sortie
        """
        pass

    def create_calibration_config(self) -> Dict[str, Any]:
        """
        Crée une configuration adaptée pour la calibration

        Returns:
            Dict[str, Any]: Configuration modifiée
        """
        calib_config = self.process_config.copy()

        start_time = datetime(2025, 1, 1, 0, 0, 0)
        end_time = start_time + timedelta(days=self.convergence_days)

        sim_config = calib_config.get('simulation', {})
        sim_config['start_time'] = start_time.isoformat()
        sim_config['end_time'] = end_time.isoformat()
        sim_config['timestep_hours'] = 1.0

        calib_config['simulation'] = sim_config
        calib_config['name'] = f"{calib_config.get('name', 'sim')}_calibration"

        if self.full_config and 'influent' in self.full_config:
            calib_config['influent'] = self.full_config['influent'].copy()
            self.logger.debug("Influent copié depuis la configuration complète")
        else:
            self.logger.warning(
                "Aucun influent trouvé dans la configuration complète. "
                "Utilisation de valeurs par défaut."
            )
            calib_config['influent'] = {
                'flowrate': 1000.0,
                'temperature': 20.0,
                'composition': {
                    'cod': 500.0,
                    'ss': 200.0,
                    'tkn': 40.0,
                    'nh4': 25.0,
                    'no3': 0.0,
                    'po4': 5.0,
                    'alkalinity': 5.0
                }
            }

        self.logger.debug(
            f"Config de calibration créée : {start_time.date()} à {end_time.date()}"
        )

        return calib_config
    
    def _extract_parameter_values(
            self,
            history: List[Any],
            param: str
    ) -> np.ndarray:
        """
        Extrait les valeurs d'un paramètre de l'historique

        Args:
            history (List[Any]): Historique des états
            param (str): Nom du paramètre

        Returns:
            np.ndarray: Array des valeurs
        """
        values = []

        for state in history:
            
            value = None

            if hasattr(state, param):
                value = getattr(state, param, None)
            elif hasattr(state, 'components') and isinstance(state.components, dict):
                value = state.components.get(param)            
            elif isinstance(state, dict):
                value = state.get(param)

            if value is not None:
                values.append(float(value))
        
        return np.array(values) if values else np.array([])
    
    def check_convergence(
            self,
            orchestrator: SimulationOrchestrator,
            window_size: Optional[int] = None
    ) -> bool:
        """
        Vérifie si la simulation a convergé

        Args:
            orchestrator (SimulationOrchestrator): Orchestrateur de simulation
            window_size (Optional[int], optional): Taille de la fenêtre (utilise convergence_window si None). Defaults to None.

        Returns:
            bool: True si convergé
        """
        if window_size is None:
            window_size = self.convergence_window

        convergence_params = self.get_convergence_parameters()

        for node_id, history in orchestrator.simulation_flow._history.items():
            if node_id == 'influent':
                continue

            if len(history) < window_size*2:
                self.logger.debug(
                    f"Historique insuffisant pour {node_id} "
                    f"({len(history)} < {window_size*2})"
                )
                return False
            
            recent_window = history[-window_size:]
            previous_window = history[-window_size*2: -window_size]

            for param in convergence_params:
                recent_values = self._extract_parameter_values(recent_window, param)
                previous_values = self._extract_parameter_values(previous_window, param)

                if not len(recent_values) or not len(previous_values):
                    continue

                recent_mean = np.mean(recent_values)
                previous_mean = np.mean(previous_values)

                if recent_mean > 1e-6:
                    relative_change = abs(
                        (recent_mean - previous_mean) / recent_mean
                    )

                    if relative_change > self.tolerance:
                        self.logger.debug(
                            f"None convergé - {node_id}.{param} : "
                            f"variation={relative_change*100:.2f}%"
                        )
                        return False
            
        self.logger.info("Convergence atteinte")
        return True
    
    def extract_steady_states(
            self,
            orchestrator: SimulationOrchestrator
    ) -> Dict[str, Dict[str, float]]:
        """
        Extrait les steady-states depuis l'historique

        Args:
            orchestrator (SimulationOrchestrator): Orchestrateur après simulation

        Returns:
            Dict[str, Dict[str, float]]: {node_id : {param: value}}
        """
        steady_states = {}
        window = self.convergence_window

        for node_id, history in orchestrator.simulation_flow._history.items():
            if node_id == 'influent':
                continue

            if not history or len(history) < window:
                self.logger.warning(
                    f"Historique insuffisant pour '{node_id}' "
                    f"({len(history)} < {window})"
                )
                continue

            final_states = history[-window:]
            steady_state = {}

            for param in self.get_key_output_parameters():
                values = self._extract_parameter_values(final_states, param)
                if len(values) > 0:
                    steady_state[param] = float(np.mean(values))
            
            steady_states[node_id] = steady_state

            self.logger.info(
                f"Steady-state extrait pour '{node_id}' : "
                f"{len(steady_state)} paramètres"
            )
        
        return steady_states
    
    def check_calibration_needed(self) -> Tuple[bool, Optional[str]]:
        """
        Vérifie is une calibration est nécessaire

        Returns:
            Tuple[bool, Optional[str]]: (needed, reason)
        """
        current_hash = self.comparator.compute_hash(self.process_config)

        if not self.cache.exists(self.process_id, self.model_type, current_hash):
            return True, "Aucune calibration en cache"
        
        cached = self.cache.load(self.process_id, self.model_type, current_hash)
        if cached is None:
            return True, "Erreur lors de la lecture du cache"
        

        if current_hash != cached.metadata.config_hash:
            config_diff = self.comparator.compare_configs(
                self.process_config,
                cached.metadata.process_config
            )

            reason = (
                f"Configuration modifiée depuis la calibration "
                f"({datetime.fromisoformat(cached.metadata.created_at).strftime('%Y-%m%d %H:%M')})\n"
            )

            if config_diff['modified']:
                reason += f"\tParamètres modifiés : {list(config_diff['modified'].keys())}\n"
            if config_diff['added']:
                reason += f"\tParamètres ajoutés : {list(config_diff['added'].keys())}\n"
            if config_diff['removed']:
                reason += f"\tParamètres supprimés : {list(config_diff['removed'].keys())}"

            return True, reason
        return False, None
    
    def run(
            self,
            skip_if_exists: bool = False,
            interactive: bool = False
    ) -> Optional[CalibrationResult]:
        """
        Lance le processus de calibration complet

        Args:
            skip_if_exists (bool, optional): Utilise la calibration existante si elle est valide. Defaults to False.
            interactive (bool, optional): Demande à l'utilisateur en cas de doute. Defaults to False.

        Returns:
            Optional[CalibrationResult]: CalibrationResult ou None
        """
        print("\n"+"="*70)
        print(f"Calibration - {self.model_type} ({self.process_id})")
        print("="*70)

        needed, reason = self.check_calibration_needed()

        current_hash = self.comparator.compute_hash(self.process_config)

        if not needed:
            print(f"\nCalibration valide et à jour")
            cached = self.cache.load(self.process_id, self.model_type, current_hash)
            if cached is not None:
                print(
                    f"\tCréée : {cached.metadata.created_at}\n"
                    f"\tConvergée : {'Oui' if cached.metadata.converged else 'Non'}\n"
                    f"\tTemps de simulation : {cached.metadata.calibration_time_hours:.1f}h\n"
                    f"\tHash config : {current_hash[:8]}"
                )
                return cached
        print(f"\nCalibration nécessaire : {reason}")

        if skip_if_exists:
            print("-> Utilisation de la dernière calibration")
            return self.cache.load(self.process_id, self.model_type, current_hash)
        
        if interactive:
            response = ask_yes_no("Lancer une nouvelle calibration ?")
            if not response:
                return self.cache.load(self.process_id, self.model_type, current_hash)
            
        return self._run_calibration()
    
    @abstractmethod
    def _run_calibration(self) -> Optional[CalibrationResult]:
        """
        Implémente la logique spécifique de calibration

        Returns:
            Optional[CalibrationResult]: CalibrationResult
        """
        pass

    def print_results(self, result: CalibrationResult) -> None:
        """Affiche un résumé des résultats de calibration"""
        meta = result.metadata

        print("\n"+"="*70)
        print("Résultats de calibration")
        print("="*70)
        print(f"\nProcédé : {meta.process_id} ({meta.model_type})")
        print(f"Créée : {meta.created_at}")
        print(f"Convergence : {'Oui' if meta.converged else 'Non'}")
        print(f"Durée simulée : {meta.calibration_time_hours:.1f} heures")
        print(f"Tolérance : {self.tolerance*100:.2f}%")

        print("\nEtats stationnaires finaux :")
        for node_id, steady_state in result.steady_states.items():
            print(f"\n\t{node_id} :")
            for param, value in steady_state.items():
                if isinstance(value, float):
                    print(f"\t{param:30s} : {value:>12.2f}")
                else:
                    print(f"\t{param:30s} : {value}")
        print("\n" + "="*70)