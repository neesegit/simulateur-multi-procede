from typing import Dict, Any

from dataclasses import dataclass

@dataclass
class CalibrationMetadata:
    """Métadonnées d'une calibration"""
    process_id: str
    model_type: str
    config_hash: str
    created_at: str
    calibration_time_hours: float
    converged: bool
    convergence_window: int
    process_config: Dict[str, Any]