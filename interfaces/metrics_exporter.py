"""
Module d'export spécialisé pour les métriques de performance
"""
import json
import pandas as pd

from pathlib import Path
from typing import Dict, Any, List
from datetime import datetime

class MetricsExporter:
    """Export spécialisé pour les métriques de traitement"""

    @staticmethod
    def export_performance_metrics(
        results: Dict[str, Any],
        output_dir: str
    ) -> Path:
        """
        Exporte un fichier JSON dédié aux métriques de performance

        Args:
            results (Dict[str, Any]): Résultats complets de simulation
            output_dir (str): Répertoire de sortie

        Returns:
            Path: Path du fichier crée
        """
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        performance_data = {
            'metadata': {
                'simulation_name': results['metadata'].get('sim_name'),
                'export_date': datetime.now().isoformat(),
                'duration_hours': results['metadata'].get('total_hours', 0)
            },
            'processes': {}
        }

        history = results.get('history', {})

        for node_id, flows in history.items():
            if node_id == 'influent' or not flows:
                continue
            
            metrics_timeline = []
            for flow in flows:
                metrics_timeline.append({
                    'timestamp': flow.get('timestamp'),
                    'cod_total': flow.get('cod', 0),
                    'cod_soluble': flow.get('cod_soluble', 0),
                    'cod_particulate': flow.get('cod_particulate', 0),
                    'cod_removal': flow.get('soluble_cod_removal', 0),
                    'biomass': flow.get('biomass_concentration', 0),
                    'mlss': flow.get('ss', 0),
                    'nh4': flow.get('nh4', 0),
                    'no3': flow.get('no3', 0),
                    'po4': flow.get('po4', 0),
                    'srt_days': flow.get('srt_days', 0) if flow.get('srt_days', 0) < float('inf') else None,
                    'svi': flow.get('svi', 0),
                    'energy_kwh': flow.get('aeration_energy_kwh', 0)
                })

            cod_soluble_values = [m['cod_soluble'] for m in metrics_timeline]
            cod_removal_values = [m['cod_removal'] for m in metrics_timeline]
            biomass_values = [m['biomass'] for m in metrics_timeline]

            performance_data['processes'][node_id] = {
                'timeline': metrics_timeline,
                'statistics': {
                    'cod_soluble': {
                        'initial': cod_soluble_values[0] if cod_soluble_values else 0,
                        'final': cod_soluble_values[-1] if cod_soluble_values else 0,
                        'average': sum(cod_soluble_values) / len(cod_soluble_values) if cod_soluble_values else 0,
                        'min': min(cod_soluble_values) if cod_soluble_values else 0,
                        'max': max(cod_soluble_values) if cod_soluble_values else 0
                    },
                    'cod_removal': {
                        'initial': cod_removal_values[0] if cod_removal_values else 0,
                        'final': cod_removal_values[-1] if cod_removal_values else 0,
                        'average': sum(cod_removal_values) / len(cod_removal_values) if cod_removal_values else 0
                    },
                    'biomass': {
                        'initial': biomass_values[0] if biomass_values else 0,
                        'final': biomass_values[-1] if biomass_values else 0,
                        'average': sum(biomass_values) / len(biomass_values) if biomass_values else 0,
                        'max': max(biomass_values) if biomass_values else 0
                    },
                    'energy': {
                        'total_kwh': sum(m['energy_kwh'] for m in metrics_timeline),
                        'total_volume_m3': len(metrics_timeline)*flows[0].get('flowrate', 0) / 60,
                        'kwh_per_m3': None
                    }
                }
            }

            energy_stats = performance_data['processes'][node_id]['statistics']['energy']
            if energy_stats['total_volume_m3'] > 0:
                energy_stats['kwh_per_m3'] = energy_stats['total_kwh'] / energy_stats['total_volume_m3']

        filename = f"performance_metrics_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        filepath = output_path / filename
        with open(filepath, 'w') as f:
            json.dump(performance_data, f, indent=2, default=str)

        return filepath
    
    @staticmethod
    def export_performance_csv(
        results: Dict[str, Any],
        output_dir: str
    ) -> Dict[str, Path]:
        """Exporte les métriques de performance en CSV (un par procédé)

        Args:
            results (Dict[str, Any]): Résultats complets
            output_dir (str): Répertoire de sortie

        Returns:
            Dict[str, Path]: Dict {node_id: chemin_csv}
        """
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        exported_files = {}
        history = results.get('history', {})

        for node_id, flows in history.items():
            if node_id == 'influent' or not flows:
                continue

            data = []
            for flow in flows:
                data.append({
                    'timestamp': flow.get('timestamp'),

                    'cod_total_mg_L': flow.get('cod', 0),
                    'cod_soluble_mg_L': flow.get('cod_soluble', 0),
                    'cod_particulate_mg_L': flow.get('cod_particulate', 0),
                    'cod_removal_percent': flow.get('soluble_cod_removal', 0),

                    'nh4_mg_L': flow.get('nh4', 0),
                    'no3_mg_L': flow.get('no3', 0),
                    'tkn_mg_L': flow.get('tkn', 0),

                    'po4_mg_L': flow.get('po4', 0),

                    'biomass_mg_L': flow.get('biomass_concentration', 0),
                    'mlss_mg_L': flow.get('ss', 0),
                    'svi_mL_g': flow.get('svi', 0),

                    'srt_days': flow.get('srt_days', 0) if flow.get('srt_days', 0) < float('inf') else None,
                    'hrt_hours': flow.get('hrt_hours', 0),

                    'aeration_energy_kwh': flow.get('aeration_energy_kwh', 0),
                    'energy_per_m3_kwh': flow.get('energy_per_m3', 0)
                })

            df = pd.DataFrame(data)
            csv_path = output_path / f"{node_id}_performance.csv"
            df.to_csv(csv_path, index=False)
            exported_files[node_id] = csv_path
        
        return exported_files
    
    @staticmethod
    def create_performance_report(
        results: Dict[str, Any],
        output_path: str
    ) -> Path:
        """
        Crée un rapport textuel de performance

        Args:
            results (Dict[str, Any]): Résultats complets
            output_path (str): Chemin du fichier de sortie

        Returns:
            Path: Path du fichier crée
        """
        path = Path(output_path)
        path.parent.mkdir(parents=True, exist_ok=True)

        with open(path, 'w', encoding='utf-8') as f:
            f.write("="*80 + "\n")
            f.write("Rapport de performance - Traitement des eaux usées\n")
            f.write("="*80 + "\n")

            metadata = results.get('metadata', {})
            f.write(f"Simulation : {metadata.get('sim_name')}\n")
            f.write(f"Période : {metadata.get('start_time')} -> {metadata.get('end_time')}\n")
            f.write(f"Durée : {metadata.get('steps_completed')} pas de temps\n\n")

            history = results.get('history', {})
            for node_id, flows in history.items():
                if node_id == 'influent' or not flows:
                    continue

                f.write("-"*80 + "\n")
                f.write(f"Procédé : {node_id}\n")
                f.write("-"*80 + "\n")

                initial = flows[0]
                final = flows[-1]

                f.write("1. Epuration de la DCO\n")
                f.write(f"\tDCO soluble initiale : {initial.get('cod_soluble', 0):>8.1f} mg/L\n")
                f.write(f"\tDCO soluble finale : {final.get('cod_soluble', 0):>8.1f} mg/L\n")
                f.write(f"\tTaux d'épuration : {final.get('soluble_cod_removal', 0):>8.1f} %\n\n")

                f.write("2. Biomasse et boues\n")
                f.write(f"\tBiomasse active : {final.get('biomass_concentration', 0):>8.1f} mg/L\n")
                f.write(f"\tMLSS : {final.get('ss', 0):>8.1f} mg/L\n")
                f.write(f"\tSRT : {final.get('srt_days', 0):>8.1f} jours\n")
                f.write(f"\tSVI : {final.get('svi', 0):>8.1f} mL/g\n\n")

                f.write("3. Azote\n")
                f.write(f"\tNH4+ finale : {final.get('nh4', 0):>8.2f} mg/L\n")
                f.write(f"\tNO3- finale : {final.get('no3', 0):>8.2f} mg/L\n\n")

                if final.get('po4') is not None:
                    f.write("4. Phosphore\n")
                    f.write(f"\tPO4 3- finale : {final.get('po4', 0):>8.2f} mg/L\n\n")

                total_energy = sum(f.get('aeration_energy_kwh', 0) for f in flows)
                f.write("5. Consommation énergétique\n")
                f.write(f"\tTotal : {total_energy:>8.1f} kWh\n")
                f.write(f"\tPar m3 traité : {final.get('energy_per_m3', 0):>8.3f} kWh/m3\n\n")

            f.write("="*80+"\n")

        return path