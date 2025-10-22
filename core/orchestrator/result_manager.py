import json

from datetime import datetime
from pathlib import Path
from typing import Dict, Any
from core.simulation_flow import SimulationFlow

class ResultManager:
    def __init__(self, simulation_flow: SimulationFlow) -> None:
        self.simulation_flow = simulation_flow
        self.results = {'metadata': {}, 'history': {}, 'statistics': {}}

    def collect(self, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """
        Finalise la simulation et prépare les résultats
        """
        self.results['metadata'] = metadata
        self.results['history'] = self.simulation_flow.export_to_dict()
        self.results['statistics'] = self._compute_statistics()
        return self.results
    
    def _compute_statistics(self) -> Dict[str, Any]:
        """
        Calcule des statistiques sur la simulation

        Returns:
            Dict[str, Any]: Dictionnaire de statistiques
        """
        stats = {}
        for nid, history in self.simulation_flow.get_all_histories().items():
            if not history:
                continue
            stats[nid] = {
                'num_samples': len(history),
                'avg_flowrate': sum(f.flowrate for f in history) / len(history),
                'avg_cod': sum(f.get('cod', 0.0) for f in history) / len(history)
            }
        return stats
    
    def save(self, output_dir: str) -> Path:
        """
        Sauvegarde les résultats de la simulation

        Args:
            output_dir (str): Répertoire de sortie

        Returns:
            Path: Chemin du fichier de résultats
        """
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        filename = f"simulation_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        filepath = output_path/filename
        with open(filepath, 'w') as f:
            json.dump(self.results, f, indent=2, default=str)
        return filepath