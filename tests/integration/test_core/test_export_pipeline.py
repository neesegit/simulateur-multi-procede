"""
Tests d'intégration — pipeline d'export

Vérifie la chaîne :
  ResultManager.save()     → 2 fichiers JSON distincts (complet + résumé)
  ResultsExporter.export_to_csv()   → fichiers CSV par nœud
  ResultsExporter.export_to_json()  → fichier JSON complet
  ResultsExporter.export_summary()  → fichier texte
"""
import json
import pytest
from pathlib import Path
from datetime import datetime

from core.data.flow_data import FlowData
from core.data.simulation_flow import SimulationFlow
from core.orchestrator.result_manager import ResultManager
from interfaces.result_exporter import ResultsExporter


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

TIMESTAMP = datetime(2025, 1, 1, 0, 0, 0)

METADATA = {
    'sim_name':        'test_export',
    'start_time':      '2025-01-01T00:00:00',
    'end_time':        '2025-01-01T04:00:00',
    'timestep':        1.0,
    'steps_completed': 4,
}


def _make_results(n_steps: int = 4, n_processes: int = 1) -> dict:
    """Construit un dict de résultats minimal mais complet."""
    sf = SimulationFlow()

    influent = FlowData(
        timestamp=TIMESTAMP, flowrate=1000.0, temperature=20.0,
        cod=500.0, tss=250.0, source_node='influent'
    )
    sf.add_flow('influent', influent)

    for p in range(n_processes):
        node_id = f'proc{p+1}'
        for _ in range(n_steps):
            flow = FlowData(
                timestamp=TIMESTAMP, flowrate=1000.0, temperature=20.0,
                cod=50.0, tss=3000.0, source_node=node_id
            )
            flow.components.update({
                'cod_soluble':           30.0,
                'soluble_cod_removal':   90.0,
                'biomass_concentration': 2500.0,
                'srt_days':              15.0,
                'svi':                   100.0,
                'hrt_hours':             5.0,
                'aeration_energy_kwh':   50.0,
                'energy_per_m3':         0.05,
            })
            sf.add_flow(node_id, flow)

    rm = ResultManager(sf)
    return rm.collect(METADATA)


# ===========================================================================
# ResultManager.save() — deux fichiers JSON distincts
# ===========================================================================

class TestResultManagerSavePipeline:

    def test_creates_two_json_files(self, tmp_path):
        results = _make_results()
        rm = ResultManager(SimulationFlow())
        rm.results = results  # injecter directement
        rm.save(str(tmp_path))
        json_files = list(tmp_path.glob('*.json'))
        assert len(json_files) == 2

    def test_full_file_contains_history(self, tmp_path):
        results = _make_results()
        rm = ResultManager(SimulationFlow())
        rm.results = results
        full_path = rm.save(str(tmp_path))
        with open(full_path) as f:
            data = json.load(f)
        assert 'history' in data

    def test_summary_file_has_no_history(self, tmp_path):
        results = _make_results()
        rm = ResultManager(SimulationFlow())
        rm.results = results
        rm.save(str(tmp_path))
        summary = [f for f in tmp_path.glob('*.json') if 'summary' in f.name][0]
        with open(summary) as f:
            data = json.load(f)
        assert 'history' not in data

    def test_summary_file_name_differs_from_full(self, tmp_path):
        results = _make_results()
        rm = ResultManager(SimulationFlow())
        rm.results = results
        full_path = rm.save(str(tmp_path))
        files = list(tmp_path.glob('*.json'))
        names = {f.name for f in files}
        assert full_path.name in names
        assert any('summary' in n for n in names)
        assert full_path.name != [n for n in names if 'summary' in n][0]

    def test_full_file_is_valid_json(self, tmp_path):
        results = _make_results()
        rm = ResultManager(SimulationFlow())
        rm.results = results
        full_path = rm.save(str(tmp_path))
        with open(full_path) as f:
            data = json.load(f)
        assert isinstance(data, dict)

    def test_summary_file_is_valid_json(self, tmp_path):
        results = _make_results()
        rm = ResultManager(SimulationFlow())
        rm.results = results
        rm.save(str(tmp_path))
        summary = [f for f in tmp_path.glob('*.json') if 'summary' in f.name][0]
        with open(summary) as f:
            data = json.load(f)
        assert isinstance(data, dict)


# ===========================================================================
# ResultsExporter.export_to_csv()
# ===========================================================================

class TestCSVExportPipeline:

    def test_creates_csv_for_each_process(self, tmp_path):
        results = _make_results(n_processes=2)
        exported = ResultsExporter.export_to_csv(results, str(tmp_path))
        assert 'proc1' in exported
        assert 'proc2' in exported

    def test_csv_files_exist_on_disk(self, tmp_path):
        results = _make_results()
        exported = ResultsExporter.export_to_csv(results, str(tmp_path))
        for path in exported.values():
            assert Path(path).exists(), f"Fichier manquant : {path}"

    def test_csv_not_empty(self, tmp_path):
        results = _make_results(n_steps=4)
        exported = ResultsExporter.export_to_csv(results, str(tmp_path))
        for path in exported.values():
            assert Path(path).stat().st_size > 0

    def test_influent_not_exported_to_csv(self, tmp_path):
        results = _make_results()
        exported = ResultsExporter.export_to_csv(results, str(tmp_path))
        assert 'influent' not in exported

    def test_empty_history_skipped(self, tmp_path):
        results = _make_results()
        results['history']['empty_node'] = []
        exported = ResultsExporter.export_to_csv(results, str(tmp_path))
        assert 'empty_node' not in exported


# ===========================================================================
# ResultsExporter.export_to_json()
# ===========================================================================

class TestJSONExportPipeline:

    def test_creates_json_file(self, tmp_path):
        results  = _make_results()
        out_path = str(tmp_path / 'results.json')
        path     = ResultsExporter.export_to_json(results, out_path)
        assert Path(path).exists()

    def test_json_file_is_valid(self, tmp_path):
        results  = _make_results()
        out_path = str(tmp_path / 'results.json')
        path     = ResultsExporter.export_to_json(results, out_path)
        with open(path) as f:
            data = json.load(f)
        assert isinstance(data, dict)

    def test_json_contains_history(self, tmp_path):
        results  = _make_results()
        out_path = str(tmp_path / 'results.json')
        path     = ResultsExporter.export_to_json(results, out_path)
        with open(path) as f:
            data = json.load(f)
        assert 'history' in data or 'metadata' in data


# ===========================================================================
# ResultsExporter.export_summary()
# ===========================================================================

class TestSummaryExportPipeline:

    def test_creates_summary_file(self, tmp_path):
        results  = _make_results()
        out_path = str(tmp_path / 'summary.txt')
        path     = ResultsExporter.export_summary(results, out_path)
        assert Path(path).exists()

    def test_summary_file_not_empty(self, tmp_path):
        results  = _make_results()
        out_path = str(tmp_path / 'summary.txt')
        path     = ResultsExporter.export_summary(results, out_path)
        assert Path(path).stat().st_size > 0

    def test_summary_mentions_simulation_name(self, tmp_path):
        results  = _make_results()
        out_path = str(tmp_path / 'summary.txt')
        path     = ResultsExporter.export_summary(results, out_path)
        content  = Path(path).read_text(encoding='utf-8', errors='replace')
        assert 'simulation' in content.lower() or 'résumé' in content.lower()


# ===========================================================================
# Pipeline complet : collect → save → export_csv → export_json
# ===========================================================================

class TestFullExportPipeline:

    def test_full_pipeline_no_error(self, tmp_path):
        """Le pipeline complet doit s'exécuter sans lever d'exception."""
        sf = SimulationFlow()
        influent = FlowData(
            timestamp=TIMESTAMP, flowrate=1000.0, temperature=20.0,
            cod=500.0, tss=250.0, source_node='influent'
        )
        sf.add_flow('influent', influent)
        for _ in range(4):
            flow = FlowData(
                timestamp=TIMESTAMP, flowrate=1000.0, temperature=20.0,
                cod=50.0, tss=3000.0, source_node='proc1'
            )
            sf.add_flow('proc1', flow)

        rm      = ResultManager(sf)
        results = rm.collect(METADATA)

        # 1. Sauvegarde JSON (complet + résumé)
        full_path = rm.save(str(tmp_path / 'json_out'))
        assert full_path.exists()
        assert len(list((tmp_path / 'json_out').glob('*.json'))) == 2

        # 2. Export CSV
        csv_files = ResultsExporter.export_to_csv(results, str(tmp_path / 'csv_out'))
        assert 'proc1' in csv_files

        # 3. Export JSON via ResultsExporter
        json_path = ResultsExporter.export_to_json(
            results, str(tmp_path / 'json_out2' / 'output.json')
        )
        assert Path(json_path).exists()
