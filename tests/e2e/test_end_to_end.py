"""
Tests end-to-end — pipeline utilisateur complet

Ces tests reproduisent l'usage réel du simulateur :
  1. Chargement d'un fichier de config (ConfigLoader.load)
  2. Exécution de la simulation (Orchestrator + ProcessFactory)
  3. Export de tous les artefacts sur disque (ResultsExporter.export_all + ResultManager.save)
  4. Vérification que les fichiers de sortie sont lisibles et cohérents

Chaque fixture utilise une simulation courte (4 pas × 30 min) pour rester rapide.
"""
import json
import pytest
import pandas as pd
from pathlib import Path

from interfaces.config import ConfigLoader
from interfaces.result_exporter import ResultsExporter
from core.orchestrator.simulation_orchestrator import SimulationOrchestrator
from core.process.process_factory import ProcessFactory


# ---------------------------------------------------------------------------
# Chemin vers les fixtures
# ---------------------------------------------------------------------------

FIXTURES = Path(__file__).parent / 'fixtures'


# ---------------------------------------------------------------------------
# Helper : charge un config et exécute la simulation
# ---------------------------------------------------------------------------

def _run_from_file(config_path: Path) -> dict:
    config = ConfigLoader.load(config_path)
    orchestrator = SimulationOrchestrator(config)
    processes    = ProcessFactory.create_from_config(config)
    for p in processes:
        orchestrator.add_process(p)
    orchestrator.initialize()
    return orchestrator.run()


# ===========================================================================
# 1. Chargement de configuration
# ===========================================================================

class TestConfigLoading:

    def test_load_valid_asm1_config(self):
        config = ConfigLoader.load(FIXTURES / 'asm1_short.json')
        assert isinstance(config, dict)
        assert config['name'] == 'e2e_asm1'

    def test_load_applies_defaults(self):
        """ConfigLoader.apply_defaults remplit les champs optionnels absents."""
        config = ConfigLoader.load(FIXTURES / 'asm1_short.json')
        assert 'simulation' in config
        assert 'influent'   in config
        assert 'processes'  in config
        assert 'connections' in config

    def test_load_settler_config(self):
        config = ConfigLoader.load(FIXTURES / 'asm1_settler_short.json')
        process_types = [p['type'] for p in config['processes']]
        assert 'ActivatedSludgeProcess'  in process_types
        assert 'SecondarySettlerProcess' in process_types

    def test_load_missing_file_raises(self, tmp_path):
        with pytest.raises(FileNotFoundError):
            ConfigLoader.load(tmp_path / 'nonexistent.json')

    def test_load_invalid_format_raises(self, tmp_path):
        bad = tmp_path / 'config.csv'
        bad.write_text('a,b,c')
        with pytest.raises(ValueError, match="non supporté"):
            ConfigLoader.load(bad)

    def test_save_then_reload_roundtrip(self, tmp_path):
        """ConfigLoader.save → ConfigLoader.load doit préserver la structure."""
        original = ConfigLoader.load(FIXTURES / 'asm1_short.json')
        saved_path = tmp_path / 'roundtrip.json'
        ConfigLoader.save(original, saved_path)
        reloaded = ConfigLoader.load(saved_path)
        assert reloaded['name']               == original['name']
        assert reloaded['simulation']['end_time'] == original['simulation']['end_time']
        assert len(reloaded['processes'])     == len(original['processes'])
        assert len(reloaded['connections'])   == len(original['connections'])

    def test_invalid_config_raises_validation_error(self, tmp_path):
        """Une config avec end_time < start_time doit être refusée."""
        bad_config = {
            'name': 'bad',
            'simulation': {
                'start_time': '2025-01-01T08:00:00',
                'end_time':   '2025-01-01T00:00:00',
                'timestep_hours': 1.0,
            },
            'influent': {'flowrate': 1000.0},
            'processes': [],
            'connections': []
        }
        path = tmp_path / 'bad.json'
        path.write_text(json.dumps(bad_config))
        with pytest.raises(Exception):
            ConfigLoader.load(path)


# ===========================================================================
# 2. Simulation ASM1 simple
# ===========================================================================

class TestE2EASM1Simple:

    @pytest.fixture(scope='class')
    def results(self):
        return _run_from_file(FIXTURES / 'asm1_short.json')

    def test_results_not_none(self, results):
        assert results is not None

    def test_metadata_present(self, results):
        assert 'metadata' in results
        assert results['metadata']['sim_name'] == 'e2e_asm1'

    def test_correct_step_count(self, results):
        """2h / 0.5h = 4 pas."""
        assert results['metadata']['steps_completed'] == 4

    def test_history_has_influent_and_bassin(self, results):
        assert 'influent' in results['history']
        assert 'bassin'   in results['history']

    def test_history_step_count_matches(self, results):
        assert len(results['history']['bassin']) == 4

    def test_flowrate_in_history(self, results):
        for step in results['history']['bassin']:
            assert step['flowrate'] == pytest.approx(1000.0, rel=0.01)

    def test_temperature_in_history(self, results):
        for step in results['history']['bassin']:
            assert step['temperature'] == pytest.approx(20.0)

    def test_no_nan_in_numeric_fields(self, results):
        import math
        for step in results['history']['bassin']:
            for key, val in step.items():
                if isinstance(val, float):
                    assert not math.isnan(val), f"NaN détecté : {key}"

    def test_summary_has_process(self, results):
        assert 'bassin' in results['summary']['performance']

    def test_statistics_avg_flowrate(self, results):
        assert results['statistics']['bassin']['avg_flowrate'] == pytest.approx(1000.0, rel=0.01)


# ===========================================================================
# 3. Simulation ASM2d simple
# ===========================================================================

class TestE2EASM2dSimple:

    @pytest.fixture(scope='class')
    def results(self):
        return _run_from_file(FIXTURES / 'asm2d_short.json')

    def test_runs_without_error(self, results):
        assert results is not None

    def test_correct_step_count(self, results):
        assert results['metadata']['steps_completed'] == 4

    def test_no_nan_in_history(self, results):
        import math
        for step in results['history']['bassin']:
            for key, val in step.items():
                if isinstance(val, float):
                    assert not math.isnan(val), f"NaN ASM2d : {key}"

    def test_sim_name_correct(self, results):
        assert results['metadata']['sim_name'] == 'e2e_asm2d'


# ===========================================================================
# 4. Simulation ASM1 + décanteur (pipeline à deux nœuds avec recyclage)
# ===========================================================================

class TestE2EASM1WithSettler:

    @pytest.fixture(scope='class')
    def results(self):
        return _run_from_file(FIXTURES / 'asm1_settler_short.json')

    def test_runs_without_error(self, results):
        assert results is not None

    def test_both_nodes_in_history(self, results):
        assert 'bassin'    in results['history']
        assert 'decanteur' in results['history']

    def test_settler_step_count(self, results):
        assert len(results['history']['decanteur']) == 4

    def test_no_nan_in_settler_history(self, results):
        import math
        for step in results['history']['decanteur']:
            for key, val in step.items():
                if isinstance(val, float):
                    assert not math.isnan(val), f"NaN décanteur : {key}"

    def test_summary_includes_both_nodes(self, results):
        perf = results['summary']['performance']
        assert 'bassin'    in perf
        assert 'decanteur' in perf


# ===========================================================================
# 5. Export complet — artefacts sur disque
# ===========================================================================

class TestE2EExportArtifacts:

    @pytest.fixture(scope='class')
    def exported(self, tmp_path_factory):
        tmp = tmp_path_factory.mktemp('export')
        results  = _run_from_file(FIXTURES / 'asm1_short.json')
        exported = ResultsExporter.export_all(results, str(tmp), name='e2e_asm1')
        return exported, tmp

    def test_export_returns_dict(self, exported):
        info, _ = exported
        assert isinstance(info, dict)

    def test_base_directory_exists(self, exported):
        info, _ = exported
        assert Path(info['base_directory']).exists()

    def test_csv_directory_exists(self, exported):
        info, _ = exported
        csv_files = info['files']['csv']
        assert len(csv_files) > 0
        for path in csv_files.values():
            assert Path(path).exists(), f"CSV manquant : {path}"

    def test_csv_file_has_rows(self, exported):
        info, _ = exported
        for path in info['files']['csv'].values():
            df = pd.read_csv(path)
            assert len(df) == 4        # 4 pas de simulation
            assert len(df.columns) > 1

    def test_json_file_exists(self, exported):
        info, _ = exported
        assert Path(info['files']['json']).exists()

    def test_json_file_is_valid(self, exported):
        info, _ = exported
        with open(info['files']['json']) as f:
            data = json.load(f)
        assert isinstance(data, dict)

    def test_json_file_contains_history(self, exported):
        info, _ = exported
        with open(info['files']['json']) as f:
            data = json.load(f)
        assert 'history' in data or 'metadata' in data

    def test_summary_txt_exists(self, exported):
        info, _ = exported
        assert Path(info['files']['summary']).exists()

    def test_summary_txt_not_empty(self, exported):
        info, _ = exported
        size = Path(info['files']['summary']).stat().st_size
        assert size > 0


# ===========================================================================
# 6. ResultManager.save() — artefacts JSON sur disque (hors export_all)
# ===========================================================================

class TestE2EResultManagerSave:

    @pytest.fixture(scope='class')
    def saved(self, tmp_path_factory):
        from core.data.simulation_flow import SimulationFlow
        from core.orchestrator.result_manager import ResultManager
        tmp     = tmp_path_factory.mktemp('rm_save')
        results = _run_from_file(FIXTURES / 'asm1_short.json')
        # Recréer un ResultManager pour tester save() indépendamment
        sf = SimulationFlow()
        rm = ResultManager(sf)
        rm.results = results
        full_path = rm.save(str(tmp))
        return full_path, tmp

    def test_full_json_exists(self, saved):
        full_path, _ = saved
        assert full_path.exists()

    def test_summary_json_exists(self, saved):
        _, tmp = saved
        summaries = list(tmp.glob('*summary*.json'))
        assert len(summaries) == 1

    def test_two_json_files_total(self, saved):
        _, tmp = saved
        assert len(list(tmp.glob('*.json'))) == 2

    def test_full_and_summary_have_different_names(self, saved):
        full_path, tmp = saved
        summary = [f for f in tmp.glob('*.json') if 'summary' in f.name][0]
        assert full_path.name != summary.name

    def test_full_json_has_history(self, saved):
        full_path, _ = saved
        with open(full_path) as f:
            data = json.load(f)
        assert 'history' in data

    def test_summary_json_has_no_history(self, saved):
        _, tmp = saved
        summary = [f for f in tmp.glob('*summary*.json')][0]
        with open(summary) as f:
            data = json.load(f)
        assert 'history' not in data


# ===========================================================================
# 7. Cohérence physique des résultats
# ===========================================================================

class TestE2EPhysicalCoherence:

    @pytest.fixture(scope='class')
    def results(self):
        return _run_from_file(FIXTURES / 'asm1_short.json')

    def test_flowrate_positive(self, results):
        for step in results['history']['bassin']:
            assert step['flowrate'] > 0

    def test_temperature_in_valid_range(self, results):
        for step in results['history']['bassin']:
            assert 0 < step['temperature'] <= 50

    def test_statistics_num_samples_is_4(self, results):
        assert results['statistics']['bassin']['num_samples'] == 4

    def test_statistics_avg_cod_positive(self, results):
        assert results['statistics']['bassin']['avg_cod'] >= 0

    def test_total_simulation_hours(self, results):
        assert results['metadata']['total_hours'] == pytest.approx(2.0)
