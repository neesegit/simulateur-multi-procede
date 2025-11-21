from typing import Dict, Any
from dataclasses import asdict
from datetime import datetime

from .dataclass.calibration_metadata import CalibrationMetadata

class CalibrationResult:
    """Résultat complet d'une calibration"""

    def __init__(
            self,
            metadata: CalibrationMetadata,
            steady_states: Dict[str, Dict[str, float]],
            simulation_results: Dict[str, Any]
    ) -> None:
        self.metadata = metadata
        self.steady_states = steady_states
        self.simulation_results = simulation_results
        self.created_at = datetime.fromisoformat(metadata.created_at)

    def to_dict(self) -> Dict[str, Any]:
        """Convertit le résultat en dictionnaire sérialisable"""
        return {
            'metadata': asdict(self.metadata),
            'steady_states': self.steady_states,
            'simulation_results': self.simulation_results
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'CalibrationResult':
        """Crée une instance depuis un disctionnaire"""
        metadata = CalibrationMetadata(**data['metadata'])
        steady_states = data['steady_states']
        simulation_results = data['simulation_results']
        return cls(metadata, steady_states, simulation_results)