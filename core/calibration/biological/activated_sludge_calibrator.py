import logging 

from typing import List, Dict, Any, Optional
from datetime import datetime

from core.calibration.calibration_result import CalibrationResult
from core.calibration.dataclass.calibration_metadata import CalibrationMetadata
from core.orchestrator.simulation_orchestrator import SimulationOrchestrator
from core.process.process_factory import ProcessFactory

from ..base_calibrator import BaseCalibrator

logger = logging.getLogger(__name__)

class ActivatedSludgeCalibrator(BaseCalibrator):
    """
    Calibrateur pour procédés de boues activées
    """
    def __init__(
            self,
            process_id: str,
            process_config: Dict[str, Any],
            model_type: str,
            full_config: Optional[Dict[str, Any]] = None,
            convergence_days: float = 200.0,
            tolerance: float = 0.01,
            check_interval: int = 50
    ) -> None:
        super().__init__(
            process_id=process_id,
            process_config=process_config,
            model_type=model_type,
            full_config=full_config,
            convergence_days=convergence_days,
            tolerance=tolerance,
            check_interval=check_interval
        )
    
    def _run_calibration(self) -> Optional[CalibrationResult]:
        """Lance la calibration pour boues activées"""
        start_time = datetime.now()

        try:
            calib_config = self.create_calibration_config()

            full_config = {
                'name': calib_config.get('name', 'calibration'),
                'description': f"Calibration pour {self.process_id}",
                'simulation': calib_config.get('simulation', {}),
                'influent': calib_config.get('influent', {}),
                'processes': [calib_config],
                'connections': calib_config.get('connections', [])
            }

            print("\nInitialisation de l'orchestrateur ...")
            orchestrator = SimulationOrchestrator(full_config)

            print("Création des procédés ...")
            processes = ProcessFactory.create_from_config(full_config)
            for process in processes:
                orchestrator.add_process(process)
                print(f"\t{process.name} ({process.node_id}) ajouté")

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
                        f"\rProgression : {progress:>6.1f}%"
                        f"({orchestrator.state.current_step}/{total_steps} pas)",
                        end='', flush=True
                    )

                if orchestrator.state.current_step % self.check_interval == 0:
                    if orchestrator.state.current_step >= 200:
                        if self.check_convergence(orchestrator):
                            converged = True
                            print(
                                f"\n\nConvergence atteinte au pas "
                                f"{orchestrator.state.current_step}\n"
                            )
                            break
            
            if not converged:
                print(
                    f"\n\nConvergence non atteinte après "
                    f"{self.convergence_days} jours\n"
                )

            steady_states = self.extract_steady_states(orchestrator)

            elapsed = (datetime.now() - start_time).total_seconds() / 3600
            config_hash = self.comparator.compute_hash(self.process_config)

            metadata = CalibrationMetadata(
                process_id=self.process_id,
                model_type=self.model_type,
                config_hash=config_hash,
                created_at=datetime.now().isoformat(),
                calibration_time_hours=elapsed,
                converged=converged,
                convergence_window=self.convergence_window,
                process_config=self.process_config
            )

            results = orchestrator.result_manager.collect({
                'sim_name': calib_config.get('name'),
                'process_id': self.process_id,
                'model_type': self.model_type,
                'calibration': True,
                'converged': converged
            })

            result = CalibrationResult(
                metadata=metadata,
                steady_states=steady_states,
                simulation_results=results
            )

            self.cache.save(result)
            self.print_results(result)

            return result
        
        except Exception as e:
            self.logger.error(f"Erreur lors de la calibration : {e}", exc_info=True)
            print(f"\nErreur : {e}")
            return None