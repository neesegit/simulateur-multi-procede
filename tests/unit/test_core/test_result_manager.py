"""
Tests unitaires pour ResultManager
"""
import json
import pytest
from datetime import datetime
from pathlib import Path

from core.data.flow_data import FlowData
from core.data.simulation_flow import SimulationFlow
from core.orchestrator.result_manager import ResultManager


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

TIMESTAMP = datetime(2025, 1, 1, 0, 0, 0)

SAMPLE_METADATA = {
    'sim_name': 'test',
    'start_time': '2025-01-01T00:00:00',
    'end_time':   '2025-01-01T08:00:00',
    'timestep':   1.0,
    'steps_completed': 8,
}


def _make_process_flow(tss=3000.0, srt=15.0, svi=100.0, hrt=5.0,
                       cod=50.0, cod_soluble=30.0, cod_removal=90.0,
                       biomass=2500.0, aeration_energy=50.0,
                       flowrate=1000.0) -> FlowData:
    """Crée un FlowData de processus avec les métriques typiques."""
    flow = FlowData(
        timestamp=TIMESTAMP,
        flowrate=flowrate,
        temperature=20.0,
        source_node='proc1',
        cod=cod,
        tss=tss,
    )
    flow.components.update({
        'cod_soluble':           cod_soluble,
        'soluble_cod_removal':   cod_removal,
        'biomass_concentration': biomass,
        'srt_days':              srt,
        'svi':                   svi,
        'hrt_hours':             hrt,
        'aeration_energy_kwh':   aeration_energy,
        'energy_per_m3':         aeration_energy / flowrate if flowrate else 0,
    })
    return flow


def _make_sim_flow(n_steps: int = 5) -> SimulationFlow:
    sf = SimulationFlow()
    influent = FlowData(
        timestamp=TIMESTAMP, flowrate=1000.0, temperature=20.0,
        cod=500.0, tss=250.0, source_node='influent'
    )
    sf.add_flow('influent', influent)
    for _ in range(n_steps):
        sf.add_flow('proc1', _make_process_flow())
    return sf


# ===========================================================================
# collect()
# ===========================================================================

class TestResultManagerCollect:

    def test_collect_returns_dict(self):
        rm = ResultManager(_make_sim_flow())
        result = rm.collect(SAMPLE_METADATA)
        assert isinstance(result, dict)

    def test_collect_has_required_keys(self):
        rm = ResultManager(_make_sim_flow())
        result = rm.collect(SAMPLE_METADATA)
        assert 'metadata'   in result
        assert 'history'    in result
        assert 'statistics' in result
        assert 'summary'    in result

    def test_collect_metadata_set(self):
        rm = ResultManager(_make_sim_flow())
        result = rm.collect(SAMPLE_METADATA)
        assert result['metadata'] == SAMPLE_METADATA

    def test_collect_history_contains_nodes(self):
        rm = ResultManager(_make_sim_flow(n_steps=3))
        result = rm.collect(SAMPLE_METADATA)
        assert 'proc1' in result['history']

    def test_collect_statistics_contains_process(self):
        rm = ResultManager(_make_sim_flow(n_steps=3))
        result = rm.collect(SAMPLE_METADATA)
        assert 'proc1' in result['statistics']

    def test_collect_statistics_num_samples(self):
        rm = ResultManager(_make_sim_flow(n_steps=7))
        result = rm.collect(SAMPLE_METADATA)
        assert result['statistics']['proc1']['num_samples'] == 7

    def test_collect_summary_has_sections(self):
        rm = ResultManager(_make_sim_flow())
        result = rm.collect(SAMPLE_METADATA)
        assert 'performance'  in result['summary']
        assert 'operational'  in result['summary']
        assert 'economic'     in result['summary']

    def test_collect_summary_performance_for_process(self):
        rm = ResultManager(_make_sim_flow())
        result = rm.collect(SAMPLE_METADATA)
        assert 'proc1' in result['summary']['performance']

    def test_collect_ignores_influent_in_summary(self):
        rm = ResultManager(_make_sim_flow())
        result = rm.collect(SAMPLE_METADATA)
        assert 'influent' not in result['summary']['performance']


# ===========================================================================
# save() — deux fichiers distincts
# ===========================================================================

class TestResultManagerSave:

    def test_save_creates_file(self, tmp_path):
        rm = ResultManager(_make_sim_flow())
        rm.collect(SAMPLE_METADATA)
        path = rm.save(str(tmp_path))
        assert path.exists()

    def test_save_returns_path_object(self, tmp_path):
        rm = ResultManager(_make_sim_flow())
        rm.collect(SAMPLE_METADATA)
        result = rm.save(str(tmp_path))
        assert isinstance(result, Path)

    def test_save_creates_summary_file(self, tmp_path):
        rm = ResultManager(_make_sim_flow())
        rm.collect(SAMPLE_METADATA)
        full_path = rm.save(str(tmp_path))
        # Le fichier résumé doit exister, avec un nom différent
        files = list(tmp_path.glob('*.json'))
        assert len(files) == 2, f"Attendu 2 fichiers JSON, trouvé {len(files)}: {files}"

    def test_full_and_summary_files_are_different(self, tmp_path):
        """Le fichier complet et le résumé ne doivent pas être le même fichier."""
        rm = ResultManager(_make_sim_flow())
        rm.collect(SAMPLE_METADATA)
        full_path = rm.save(str(tmp_path))
        files = list(tmp_path.glob('*.json'))
        assert len(files) == 2
        names = {f.name for f in files}
        assert full_path.name in names
        summary_name = [n for n in names if n != full_path.name][0]
        assert 'summary' in summary_name

    def test_summary_file_contains_less_data(self, tmp_path):
        """Le fichier résumé doit être plus léger que le fichier complet."""
        rm = ResultManager(_make_sim_flow(n_steps=10))
        rm.collect(SAMPLE_METADATA)
        full_path = rm.save(str(tmp_path))
        files = list(tmp_path.glob('*.json'))
        summary_path = [f for f in files if 'summary' in f.name][0]
        assert full_path.stat().st_size > summary_path.stat().st_size

    def test_summary_file_has_no_history(self, tmp_path):
        """Le fichier résumé ne doit pas contenir 'history'."""
        rm = ResultManager(_make_sim_flow())
        rm.collect(SAMPLE_METADATA)
        rm.save(str(tmp_path))
        summary_path = list(tmp_path.glob('*summary*.json'))[0]
        with open(summary_path) as f:
            data = json.load(f)
        assert 'history' not in data

    def test_save_creates_output_dir_if_missing(self, tmp_path):
        new_dir = tmp_path / 'deep' / 'nested'
        rm = ResultManager(_make_sim_flow())
        rm.collect(SAMPLE_METADATA)
        rm.save(str(new_dir))
        assert new_dir.exists()


# ===========================================================================
# _classify_efficiency()
# ===========================================================================

class TestClassifyEfficiency:

    @pytest.fixture
    def rm(self):
        return ResultManager(SimulationFlow())

    @pytest.mark.parametrize('removal,expected', [
        (97.0, 'Excellent'),
        (92.0, 'Très bon'),
        (85.0, 'Bon'),
        (75.0, 'Moyen'),
        (50.0, 'Insuffisant'),
        (95.0, 'Excellent'),   # borne exacte
        (90.0, 'Très bon'),    # borne exacte
        (80.0, 'Bon'),         # borne exacte
        (70.0, 'Moyen'),       # borne exacte
    ])
    def test_thresholds(self, rm, removal, expected):
        assert rm._classify_efficiency(removal) == expected


# ===========================================================================
# _classify_operation()
# ===========================================================================

class TestClassifyOperation:

    @pytest.fixture
    def rm(self):
        return ResultManager(SimulationFlow())

    def test_optimal_conditions(self, rm):
        flow = _make_process_flow(tss=3000.0, srt=15.0, svi=100.0)
        assert rm._classify_operation(flow) == 'Optimal'

    def test_low_mlss_warning(self, rm):
        flow = _make_process_flow(tss=1000.0, srt=15.0, svi=100.0)
        result = rm._classify_operation(flow)
        assert 'MLSS faible' in result

    def test_high_mlss_warning(self, rm):
        flow = _make_process_flow(tss=6000.0, srt=15.0, svi=100.0)
        result = rm._classify_operation(flow)
        assert 'MLSS élevé' in result

    def test_high_svi_warning(self, rm):
        flow = _make_process_flow(tss=3000.0, srt=15.0, svi=250.0)
        result = rm._classify_operation(flow)
        assert 'décantabilité' in result.lower()

    def test_short_srt_warning(self, rm):
        flow = _make_process_flow(tss=3000.0, srt=1.0, svi=100.0)
        result = rm._classify_operation(flow)
        assert 'SRT trop court' in result

    def test_long_srt_warning(self, rm):
        flow = _make_process_flow(tss=3000.0, srt=40.0, svi=100.0)
        result = rm._classify_operation(flow)
        assert 'SRT très élevé' in result

    def test_multiple_issues_combined(self, rm):
        flow = _make_process_flow(tss=1000.0, srt=1.0, svi=100.0)
        result = rm._classify_operation(flow)
        assert 'Problèmes' in result

    def test_single_issue_uses_attention_prefix(self, rm):
        flow = _make_process_flow(tss=1000.0, srt=15.0, svi=100.0)
        result = rm._classify_operation(flow)
        assert result.startswith('Attention')
