"""
Classe de base abstraite pour les calibrateurs
Définit l'interface commune pour tous les types de procédés
"""
import logging
import numpy as np


from abc import ABC, abstractmethod
from typing import Dict, Any, Tuple, Optional, List
from datetime import datetime, timedelta

from core.orchestrator.simulation_orchestrator import SimulationOrchestrator
from core.process.process_factory import ProcessFactory

logger = logging.getLogger(__name__)

class BaseCalibrator(ABC):
    """
    Classe abstraite pour la calibration steady-state

    Définie l'interface générique pour calibrer n'importe quel type de procédé
    """

    def __init__(
            self,
            config: Dict[str, Any],
            convergence_days: float = 200.0,
            tolerance: float = 0.01,
            check_interval: int = 50,
            process_type: str = "unknown"
    ) -> None:
        """
        Initialise le calibrateur

        Args:
            config (Dict[str, Any]): Configuration de simulation
            convergence_days (float, optional): Durée maximale de simulation. Defaults to 200.0.
            tolerance (float, optional): Tolérance de convergence. Defaults to 0.01.
            check_interval (int, optional): Intervalle de vérification. Defaults to 50.
            process_type (str, optional): Type de procédé. Defaults to "unknown".
        """
        self.config = config
        self.convergence_days = convergence_days
        self.tolerance = tolerance
        self.check_interval = check_interval
        self.process_type = process_type

        logger.info(
            f"Calibrateur {process_type} initialisé : "
            f"{convergence_days} jours, tolérance={tolerance*100:.1f}%"
        )

    @abstractmethod
    def get_convergence_parameters(self) -> List[str]:
        """
        Retourne la liste des paramètres à vérifier pour la convergence

        Returns:
            List[str]: Liste de noms de paramètres
        """
        pass

    @abstractmethod
    def get_key_output_parameters(self) -> List[str]:
        """
        Retourne les paramètres clés à extraire pour les steady-states

        Returns:
            List[str]: Liste de noms de paramètres
        """
        pass

    def create_calibration_config(self) -> Dict[str, Any]:
        """
        Crée une configuration adaptée pour la calibration

        Returns:
            Dict[str, Any]: Configuration modifiée pour calibration
        """
        calib_config = self.config.copy()

        sim_config = calib_config.get('simulation', {})

        start_time = datetime.fromisoformat(
            sim_config.get('start_time', '2025-01-01T00:00:00')
        )

        end_time = start_time + timedelta(days=self.convergence_days)

        sim_config['start_time'] = start_time.isoformat()
        sim_config['end_time'] = end_time.isoformat()
        sim_config['timestep_hours'] = 1.0
        calib_config['simulation'] = sim_config
        calib_config['name'] = f"{calib_config.get('name', 'sim')}_calibration"

        logger.debug(f"Config de calibration créée : {start_time} à {end_time}")

        return calib_config
    
    def check_convergence(
            self,
            orchestrator: SimulationOrchestrator,
            window_size: int = 50
    ) -> bool:
        """
        Vérifie si la simulation a convergé

        Args:
            orchestrator (SimulationOrchestrator): Orchestrateur de simulation
            window_size (int, optional): Taille de la fenêtre de vérification. Defaults to 50.

        Returns:
            bool: True si convergé
        """
        convergence_params = self.get_convergence_parameters()

        for node_id, history in orchestrator.simulation_flow._history.items():
            if node_id == 'influent':
                continue

            if len(history) < window_size*2:
                logger.debug(
                    f"Historique insuffisant pour {node_id} "
                    f"({len(history)} < {window_size*2})"
                )
                return False
            
            recent_window = history[-window_size:]
            previous_window = history[-window_size*2: -window_size]
            
            for param in convergence_params:
                recent_values = self._extract_parameter_values(
                    recent_window, param
                )
                previous_values = self._extract_parameter_values(
                    previous_window, param
                )

                if not recent_values or not previous_values:
                    continue

                recent_mean = np.mean(recent_values)
                previous_mean = np.mean(previous_values)

                if recent_mean > 1e-6:
                    relative_change = abs(
                        (recent_mean - previous_mean) / recent_mean
                    )
                    if relative_change > self.tolerance:
                        logger.debug(
                            f"Non convergé - {node_id}.{param} : "
                            f"variation={relative_change*100:.2f}"
                        )
                        return False
                    
        logger.info("Convergence atteinte")
        return True

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
            np.ndarray: Array numpy des valeurs
        """
        values = []
        for state in history:
            if hasattr(state, param):
                value = getattr(state, param, None)
                if value is not None:
                    values.append(value)
                    continue

            if hasattr(state, 'components') and isinstance(state.components, dict):
                value = state.components.get(param)
                if value is not None:
                    values.append(value)
                    continue

            if isinstance(state, dict):
                value = state.get(param)
                if value is not None:
                    values.append(value)
                    continue
            
        return np.array(values)
    
    def run_calibration(self) -> Dict[str, Any]:
        """
        Exécute la calibration steady-state

        Returns:
            Dict[str, Any]: Résultats de la simulation de calibration
        """
        print("\n" + "="*70)
        print(f"Calibration {self.process_type}")
        print("="*70)
        print(f"\nDurée maximale: {self.convergence_days} jours")
        print(f"Tolérance : {self.tolerance*100:.1f}%")
        print(f"Vérification : tous les {self.check_interval} pas")
        print(f"Paramètres clés : {', '.join(self.get_convergence_parameters())}")

        calib_config = self.create_calibration_config()

        print("\nInitialisation de l'orchestrateur ...")
        orchestrator = SimulationOrchestrator(calib_config)

        print("Création des procédés ...")
        processes = ProcessFactory.create_from_config(calib_config)
        for process in processes:
            orchestrator.add_process(process)
            print(f"\t- {process.name} ({process.node_id})")

        orchestrator.initialize()

        print("\n"+"-"*70)
        print("Simulation de calibration en cours ...")
        print("-"*70)

        total_steps = orchestrator.state.total_steps
        converged = False

        while orchestrator.state.current_time < orchestrator.state.end_time:
            orchestrator._run_timestep()
            orchestrator.state.advance()

            if orchestrator.state.current_step % 100 == 0:
                progress = orchestrator.state.progress_percent()
                print(
                    f"\tProgression : {progress:.1f}% "
                    f"({orchestrator.state.current_step}/{total_steps} pas)"
                )

            if orchestrator.state.current_step % self.check_interval == 0:
                if orchestrator.state.current_step >= 200:
                    if self.check_convergence(orchestrator):
                        converged = True
                        print(
                            "\nConvergence atteinte au pas "
                            f"{orchestrator.state.current_step}"
                        )
                        break
            
        if not converged:
            print(
                "\nConvergence non atteinte après "
                f"{self.convergence_days} jours"
            )
            logger.warning(
                f"Calibration {self.process_type} terminée sans convergence"
            )

        metadata = {
            'sim_name': calib_config.get('name'),
            'process_type': self.process_type,
            'start_time': str(orchestrator.state.start_time),
            'end_time': str(orchestrator.state.current_time),
            'total_hours': (
                orchestrator.state.current_time - orchestrator.state.start_time
            ).total_seconds() / 3600,
            'timestep': orchestrator.state.timestep,
            'steps_completed': orchestrator.state.current_step,
            'converged': converged
        }

        results = orchestrator.result_manager.collect(metadata)

        print("\n"+"="*70)
        print("Calibration terminée")
        print("="*70)

        return results
    
    def print_calibration_results(self, results: Dict[str, Any]) -> None:
        """
        Affiche un résumé des résultats de calibration

        Args:
            results (Dict[str, Any]): Résultats de calibration
        """
        print("\n"+"-"*70)
        print("Résumé de calibration")
        print("-"*70)

        metadata = results.get('metadata', {})
        print(f"\nType procédé : {metadata.get('process_type', 'unknown')}")
        print(f"Durée simulée : {metadata.get('total_hours', 0):.1f} heures")
        print(f"Pas effectués : {metadata.get('steps_completed', 0)}")
        print(f"Convergence : {'Oui' if metadata.get('converged') else 'Non'}")

        stats = results.get('statistics', {})

        if stats:
            print("\nEtats finaux des procédés :")
            for node_id, node_stats in stats.items():
                if node_id == 'influent':
                    continue

                print(f"\n\t{node_id} :")
                for param in self.get_key_output_parameters():
                    key = f"avg_{param}" if param != 'num_samples' else param
                    if key in node_stats:
                        value = node_stats[key]
                        if isinstance(value, float):
                            print(f"\t\t{param:20s} : {value:>10.2f}")
                        else:
                            print(f"\t\t{param:20s} : {value:>10}")

        print("\n"+"-"*70)

    def extract_steady_states(
            self,
            results: Dict[str, Any],
            convergence_window: int = 100
    ) -> Dict[str, Dict[str, float]]:
        """
        Extrait les steady-states depuis les résultats

        Args:
            results (Dict[str, Any]): Résultats de simulation
            convergence_window (int, optional): Nombre de points à moyenner. Defaults to 100.

        Returns:
            Dict[str, Dict[str, float]]: Dictionnaire des steady-states par noeud
        """
        steady_states = {}

        history = results.get('history', {})

        for node_id, node_history in history.items():
            if node_id == 'influent':
                continue

            if not node_history or len(node_history) < convergence_window:
                logger.warning(
                    f"Historique insuffisant pour '{node_id}' "
                    f"({len(node_history)} < {convergence_window})"
                )
                continue

            final_states = node_history[-convergence_window:]
            steady_state = {}

            all_parameters = self._get_all_parameters(final_states)
            for param in all_parameters:
                values = self._extract_parameter_values(final_states, param)
                if len(values) > 0:
                    steady_state[param] = float(np.mean(values))
            
            steady_states[node_id] = steady_state

            logger.info(
                f"Steady-state extrait pour '{node_id}' "
                f"{len(steady_state)} paramètres"
            )

        return steady_states

    def _get_all_parameters(self, states: List[Any]) -> set:
        """
        Identifie tous les paramètres présents dans les états

        Args:
            states (List[Any]): Liste des états

        Returns:
            set: Set de noms de paramètres
        """
        all_params = set()

        for state in states:
            if hasattr(state, '__dict__'):
                all_params.update(state.__dict__.keys())

            if hasattr(state, 'components') and isinstance(state.components, dict):
                all_params.update(state.components.keys())

            if isinstance(state, dict):
                all_params.update(state.keys())

        return all_params