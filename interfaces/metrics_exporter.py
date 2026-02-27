"""
Module d'export spécialisé pour les métriques de performance
"""
import json
import pandas as pd

from pathlib import Path
from typing import Dict, Any, List
from datetime import datetime

def safe_get(flow: dict, key: str, default=0) -> float:
    if isinstance(flow, dict):
        return flow.get(key, flow.get('components', {}).get(key, default))
    return getattr(flow, key, default)



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
                    'timestamp': safe_get(flow, 'timestamp'),
                    'cod_total': safe_get(flow, 'cod'),
                    'cod_soluble': safe_get(flow, 'cod_soluble', 0),
                    'cod_particulate': safe_get(flow, 'cod_particulate', 0),
                    'cod_removal': safe_get(flow, 'cod_removal_rate', 0),
                    'biomass': safe_get(flow, 'biomass_concentration', 0),
                    'mlss': safe_get(flow, 'mlss', 0), #or safe_get(flow, 'tss', 0),
                    'nh4': safe_get(flow, 'nh4', 0),
                    'no3': safe_get(flow, 'no3', 0),
                    'po4': safe_get(flow, 'po4', 0),
                    'srt_days': safe_get(flow, 'srt_days', 0) if safe_get(flow, 'srt_days', 0) < float('inf') else None,
                    'svi': safe_get(flow, 'svi', 0),
                    'energy_kwh': safe_get(flow, 'aeration_energy_kwh', 0)
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

                    'cod_total_mg_L': safe_get(flow, 'cod', 0),
                    'cod_soluble_mg_L': safe_get(flow, 'cod_soluble', 0),
                    'cod_particulate_mg_L': safe_get(flow, 'cod_particulate', 0),
                    'soluble_cod_removal_percent': safe_get(flow, 'soluble_cod_removal', 0),

                    'nh4_mg_L': safe_get(flow, 'nh4', 0),
                    'no3_mg_L': safe_get(flow, 'no3', 0),
                    'tkn_mg_L': safe_get(flow, 'tkn', 0),

                    'po4_mg_L': safe_get(flow, 'po4', 0),

                    'biomass_mg_L': safe_get(flow, 'biomass_concentration', 0),
                    'mlss_mg_L': safe_get(flow, 'mlss', 0),
                    'svi_mL_g': safe_get(flow, 'svi', 0),

                    'srt_days': safe_get(flow, 'srt_days', 0) if safe_get(flow, 'srt_days', 0) < float('inf') else None,
                    'hrt_hours': safe_get(flow, 'hrt_hours', 0),

                    'aeration_energy_kwh': safe_get(flow, 'aeration_energy_kwh', 0),
                    'energy_per_m3_kwh': safe_get(flow, 'energy_per_m3', 0)
                })

            df = pd.DataFrame(data)
            csv_path = output_path / f"{node_id}_performance.csv"
            df.to_csv(csv_path, index=False)
            exported_files[node_id] = csv_path
        
        return exported_files
    
    @staticmethod
    def _write_bioreactor_report(f, flows: List[dict]) -> None:
        """Sections du rapport pour un bassin à boues activées."""
        initial = flows[0]
        final   = flows[-1]

        f.write("1. Epuration de la DCO\n")
        f.write(f"\tDCO soluble initiale : {safe_get(initial, 'cod_soluble', 0):>8.1f} mg/L\n")
        f.write(f"\tDCO soluble finale   : {safe_get(final,   'cod_soluble', 0):>8.1f} mg/L\n")
        f.write(f"\tTaux d'épuration     : {safe_get(final,   'soluble_cod_removal', 0):>8.1f} %\n\n")

        f.write("2. Biomasse et boues\n")
        f.write(f"\tBiomasse active : {safe_get(final, 'biomass_concentration', 0):>8.1f} mg/L\n")
        f.write(f"\tMLSS            : {safe_get(final, 'tss', 0):>8.1f} mg/L\n")
        f.write(f"\tSRT             : {safe_get(final, 'srt_days', 0):>8.1f} jours\n")
        f.write(f"\tSVI             : {safe_get(final, 'svi', 0):>8.1f} mL/g\n\n")

        f.write("3. Azote\n")
        f.write(f"\tNH4+ finale : {safe_get(final, 'nh4', 0):>8.2f} mg/L\n")
        f.write(f"\tNO3- finale : {safe_get(final, 'no3', 0):>8.2f} mg/L\n\n")

        f.write("4. Phosphore\n")
        f.write(f"\tPO4 3- finale : {safe_get(final, 'po4', 0):>8.2f} mg/L\n\n")

        total_energy = sum(safe_get(step, 'aeration_energy_kwh', 0) for step in flows)
        f.write("5. Consommation énergétique\n")
        f.write(f"\tTotal          : {total_energy:>8.1f} kWh\n")
        f.write(f"\tPar m3 traité  : {safe_get(final, 'energy_per_m3', 0):>8.3f} kWh/m3\n\n")

    @staticmethod
    def _write_settler_report(f, flows: List[dict]) -> None:
        """Sections du rapport pour un décanteur secondaire (TakacsModel)."""
        final = flows[-1]

        x_overflow  = safe_get(final, 'X_overflow',  0) or safe_get(final, 'tss', 0)
        x_underflow = safe_get(final, 'X_underflow',  0)
        removal     = safe_get(final, 'removal_efficiency', 0)
        surf_load   = safe_get(final, 'surface_loading', 0)
        solids_load = safe_get(final, 'solids_loading', 0)
        q_overflow  = safe_get(final, 'flowrate', 0)

        f.write("1. Séparation des boues\n")
        f.write(f"\tTaux d'élimination TSS : {removal:>8.1f} %\n")
        f.write(f"\tTSS surnageant         : {x_overflow:>8.1f} mg/L\n")
        f.write(f"\tTSS boues (underflow)  : {x_underflow:>8.1f} mg/L\n\n")

        f.write("2. Charges hydrauliques\n")
        f.write(f"\tCharge de surface      : {surf_load:>8.3f} m/h\n")
        f.write(f"\tCharge en solides      : {solids_load:>8.3f} kg/(m²·h)\n")
        f.write(f"\tDébit surnageant       : {q_overflow:>8.1f} m3/h\n\n")

        # Voile de boues (info optionnelle)
        sludge_blanket = final.get('sludge_blanket', {}) if isinstance(final, dict) else {}
        if sludge_blanket and sludge_blanket.get('has_blanket'):
            top_layer   = sludge_blanket.get('blanket_top_layer', '—')
            thickness   = sludge_blanket.get('blanket_thickness_layers', '—')
            max_conc    = sludge_blanket.get('max_concentration', 0)
            f.write("3. Voile de boues\n")
            f.write(f"\tCouche supérieure      : {top_layer}\n")
            f.write(f"\tÉpaisseur (couches)    : {thickness}\n")
            f.write(f"\tConcentration max      : {max_conc:.1f} mg/L\n\n")
        else:
            f.write("3. Voile de boues\n")
            f.write("\tAucun voile détecté\n\n")

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

                final = flows[-1]
                model_type = final.get('model_type', '') if isinstance(final, dict) else ''

                if model_type == 'TakacsModel':
                    MetricsExporter._write_settler_report(f, flows)
                else:
                    MetricsExporter._write_bioreactor_report(f, flows)

            f.write("="*80+"\n")

        return path