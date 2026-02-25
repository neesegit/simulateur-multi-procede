import json
import numpy as np

from datetime import datetime
from pathlib import Path
from typing import Dict, Any
from core.data.simulation_flow import SimulationFlow
from core.data.flow_data import FlowData

class ResultManager:
    def __init__(self, simulation_flow: SimulationFlow) -> None:
        self.simulation_flow = simulation_flow
        self.results = {'metadata': {}, 'history': {}, 'statistics': {}, 'summary': {}}

    def collect(self, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """
        Finalise la simulation et prépare les résultats
        """
        self.results['metadata'] = metadata
        self.results['history'] = self.simulation_flow.export_to_dict()
        self.results['statistics'] = self._compute_statistics()
        self.results['summary'] = self._compute_summary()
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

            if nid != 'influent':
                cod_soluble_values = [f.get('cod_soluble', 0) for f in history]
                cod_removal_values = [f.get('soluble_cod_removal', 0) for f in history]
                biomass_values = [f.get('biomass_concentration', 0) for f in history]
                srt_values = [f.get('srt_days', 0) for f in history if f.get('srt_days', 0) < float('inf')]

                stats[nid].update({
                    'avg_cod_soluble': np.mean(cod_soluble_values) if cod_soluble_values else 0,
                    'min_cod_soluble': np.min(cod_soluble_values) if cod_soluble_values else 0,
                    'max_cod_soluble': np.max(cod_soluble_values) if cod_soluble_values else 0,

                    'avg_cod_removal': np.mean(cod_removal_values) if cod_removal_values else 0,
                    'min_cod_removal': np.min(cod_removal_values) if cod_removal_values else 0,
                    'max_cod_removal': np.max(cod_removal_values) if cod_removal_values else 0,

                    'avg_biomass': np.mean(biomass_values) if biomass_values else 0,
                    'min_biomass': np.min(biomass_values) if biomass_values else 0,
                    'max_biomass': np.max(biomass_values) if biomass_values else 0,

                    'avg_srt_days': np.mean(srt_values) if srt_values else 0,

                    'total_energy_kwh': sum(f.get('aeration_energy_kwh', 0) for f in history),
                    'avg_energy_per_m3': np.mean([f.get('energy_per_m3', 0) for f in history])
                })

        return stats
    
    def _compute_summary(self) -> Dict[str, Any]:
        """
        Calcule un résumé global de la simulation
        """
        summary = {
            'performance': {},
            'operational': {},
            'economic': {}
        }

        histories = self.simulation_flow.get_all_histories()

        for nid, history in histories.items():
            if nid == 'influent' or not history:
                continue

            final = history[-1]

            summary['performance'][nid] = {
                'final_cod_total': final.get('cod', 0),
                'final_cod_soluble': final.get('cod_soluble', 0),
                'final_cod_removal': final.get('soluble_cod_removal', 0),
                'final_nh4': final.get('nh4', 0),
                'final_no3': final.get('no3', 0),
                'final_po4': final.get('po4', 0),
                'treatment_efficiency': self._classify_efficiency(final.get('soluble_cod_removal', 0))
            }

            summary['operational'][nid] = {
                'mlss': final.get('tss', 0),
                'biomass': final.get('biomass_concentration', 0),
                'srt_days': final.get('srt_days', 0),
                'svi': final.get('svi', 0),
                'hrt_hours': final.get('hrt_hours', 0),
                'operational_status': self._classify_operation(final)
            }

            total_energy = sum(f.get('aeration_energy_kwh', 0) for f in history)
            total_volume = sum(f.get('flowrate', 0)*(1/60) for f in history)

            summary['economic'][nid] = {
                'total_energy_kwh': total_energy,
                'total_volume_m3': total_volume,
                'energy_per_m3': total_energy / total_volume if total_volume > 0 else 0,
                'estimated_cost_eur': total_energy * 0.15, # 0.15 €/kwh
                'cost_per_m3': (total_energy*0.15) / total_volume if total_volume > 0 else 0
            }

        return summary

    def _classify_efficiency(self, removal_rate: float) -> str:
        """Classifie l'efficacité du traitement"""
        if removal_rate >= 95:
            return "Excellent"
        elif removal_rate >= 90:
            return "Très bon"
        elif removal_rate >= 80:
            return "Bon"
        elif removal_rate >= 70:
            return "Moyen"
        else:
            return "Insuffisant"
        
    def _classify_operation(self, data: FlowData) -> str:
        """Evalue l'état opérationnel"""
        issues = []

        mlss = data.get('tss', 0)
        if mlss < 1500:
            issues.append("MLSS faible")
        elif mlss > 5000:
            issues.append("MLSS élevé")

        svi = data.get('svi', 0)
        if svi > 200:
            issues.append("Mauvaise décantabilité")

        srt = data.get('srt_days', 0)
        if srt < 3:
            issues.append("SRT trop court")
        elif srt > 30:
            issues.append("SRT très élevé")

        if not issues:
            return "Optimal"
        elif len(issues) == 1:
            return f"Attention : {issues[0]}"
        else:
            return f"Problèmes : {', '.join(issues)}"

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

        summary_file = output_path / filename.replace('_full.json', '_summary.json')
        with open(summary_file, 'w') as f:
            summary_data = {
                'metadata': self.results['metadata'],
                'statistics': self.results['statistics'],
                'summary': self.results['summary']
            }
            json.dump(summary_data, f, indent=2, default=str)
        return filepath