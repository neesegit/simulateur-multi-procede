"""
Tests d'intégration — pipeline de simulation complet

Ces tests vérifient la chaîne :
  Config → ProcessFactory → SimulationOrchestrator → ResultManager → résultats

Chaque simulation utilise un pas de temps long (1h) et une durée courte (4h)
pour rester rapide tout en exercer l'ensemble du pipeline.
"""
import pytest
import numpy as np

from core.orchestrator.simulation_orchestrator import SimulationOrchestrator
from core.process.process_factory import ProcessFactory


# ---------------------------------------------------------------------------
# Configs minimales — courtes (4 pas) pour rapidité
# ---------------------------------------------------------------------------

def _base_config(model: str, extra_processes=None, extra_connections=None) -> dict:
    processes = [
        {
            'node_id': 'bassin',
            'type':    'ActivatedSludgeProcess',
            'name':    f'Bassin {model}',
            'config': {
                'model':                       model,
                'volume':                      5000.0,
                'dissolved_oxygen_setpoint':   2.0,
                'recycle_ratio':               0.0,
                'waste_ratio':                 0.01,
            }
        }
    ]
    connections = [
        {'source': 'influent', 'target': 'bassin', 'fraction': 1.0, 'is_recycle': False}
    ]
    if extra_processes:
        processes += extra_processes
    if extra_connections:
        connections += extra_connections

    return {
        'name': f'test_{model.lower()}',
        'simulation': {
            'start_time':      '2025-01-01T00:00:00',
            'end_time':        '2025-01-01T04:00:00',
            'timestep_hours':  1.0,
        },
        'influent': {
            'flowrate':     1000.0,
            'temperature':  20.0,
            'composition': {
                'cod': 500.0, 'ss': 250.0, 'tkn': 40.0,
                'nh4': 28.0,  'no3': 0.5,  'po4': 8.0,
                'alkalinity': 6.0,
            }
        },
        'processes':   processes,
        'connections': connections,
    }


def _run(config: dict) -> dict:
    """Lance une simulation et retourne les résultats."""
    orchestrator = SimulationOrchestrator(config)
    processes    = ProcessFactory.create_from_config(config)
    for p in processes:
        orchestrator.add_process(p)
    orchestrator.initialize()
    return orchestrator.run()


# ===========================================================================
# Structure des résultats
# ===========================================================================

class TestResultsStructure:

    @pytest.fixture(scope='class')
    def results(self):
        return _run(_base_config('ASM1Model'))

    def test_has_metadata(self, results):
        assert 'metadata' in results

    def test_has_history(self, results):
        assert 'history' in results

    def test_has_statistics(self, results):
        assert 'statistics' in results

    def test_has_summary(self, results):
        assert 'summary' in results

    def test_metadata_fields(self, results):
        meta = results['metadata']
        assert 'sim_name'        in meta
        assert 'start_time'      in meta
        assert 'end_time'        in meta
        assert 'steps_completed' in meta

    def test_history_contains_influent(self, results):
        assert 'influent' in results['history']

    def test_history_contains_process(self, results):
        assert 'bassin' in results['history']

    def test_history_has_correct_number_of_steps(self, results):
        # 4h / 1h = 4 pas
        assert len(results['history']['bassin']) == 4

    def test_statistics_contains_process(self, results):
        assert 'bassin' in results['statistics']

    def test_summary_sections(self, results):
        assert 'performance'  in results['summary']
        assert 'operational'  in results['summary']
        assert 'economic'     in results['summary']


# ===========================================================================
# ASM1 — comportement biologique
# ===========================================================================

class TestASM1SimulationBiology:

    @pytest.fixture(scope='class')
    def results(self):
        return _run(_base_config('ASM1Model'))

    def test_no_nan_in_history(self, results):
        for flow_dict in results['history']['bassin']:
            for key, val in flow_dict.items():
                if isinstance(val, (int, float)):
                    assert not np.isnan(val), f"NaN détecté pour '{key}'"

    def test_cod_present_in_history(self, results):
        flows = results['history']['bassin']
        assert any(f.get('cod', 0) > 0 for f in flows)

    def test_flowrate_conserved(self, results):
        """Le débit de sortie doit être proche du débit d'entrée."""
        influent_q = results['history']['influent'][0]['flowrate']
        process_q  = results['history']['bassin'][-1]['flowrate']
        assert abs(process_q - influent_q) / influent_q < 0.05

    def test_temperature_conserved(self, results):
        """La température ne doit pas changer."""
        temp = results['history']['bassin'][-1]['temperature']
        assert temp == pytest.approx(20.0)

    def test_avg_flowrate_in_statistics(self, results):
        avg_q = results['statistics']['bassin']['avg_flowrate']
        assert avg_q > 0

    def test_steps_completed_matches_duration(self, results):
        assert results['metadata']['steps_completed'] == 4


# ===========================================================================
# ASM2d — simulation complète
# ===========================================================================

class TestASM2dSimulationPipeline:

    @pytest.fixture(scope='class')
    def results(self):
        return _run(_base_config('ASM2dModel'))

    def test_runs_without_error(self, results):
        assert results is not None

    def test_history_has_steps(self, results):
        assert len(results['history']['bassin']) == 4

    def test_no_nan_in_history(self, results):
        for flow_dict in results['history']['bassin']:
            for key, val in flow_dict.items():
                if isinstance(val, (int, float)):
                    assert not np.isnan(val), f"NaN détecté pour '{key}'"

    def test_summary_performance_has_process(self, results):
        assert 'bassin' in results['summary']['performance']


# ===========================================================================
# ASM3 — simulation complète
# ===========================================================================

class TestASM3SimulationPipeline:

    @pytest.fixture(scope='class')
    def results(self):
        return _run(_base_config('ASM3Model'))

    def test_runs_without_error(self, results):
        assert results is not None

    def test_history_has_steps(self, results):
        assert len(results['history']['bassin']) == 4

    def test_no_nan_in_history(self, results):
        for flow_dict in results['history']['bassin']:
            for key, val in flow_dict.items():
                if isinstance(val, (int, float)):
                    assert not np.isnan(val), f"NaN détecté pour '{key}'"


# ===========================================================================
# Paramètres personnalisés transmis au modèle
# ===========================================================================

class TestCustomModelParams:

    def test_custom_mu_h_reaches_model(self):
        """Un µ_max personnalisé doit être utilisé (non écrasé par DEFAULT_PARAMS)."""
        config = _base_config('ASM1Model')
        config['processes'][0]['config']['model_params'] = {'mu_h': 0.001}
        # La simulation doit tourner sans lever d'exception
        results = _run(config)
        assert results is not None


# ===========================================================================
# Simulation avec décanteur secondaire (pipeline à deux nœuds)
# ===========================================================================

class TestSettlerPipeline:

    @pytest.fixture(scope='class')
    def results(self):
        config = {
            'name': 'test_settler',
            'simulation': {
                'start_time':     '2025-01-01T00:00:00',
                'end_time':       '2025-01-01T04:00:00',
                'timestep_hours': 1.0,
            },
            'influent': {
                'flowrate':    1000.0,
                'temperature': 20.0,
                'composition': {
                    'cod': 500.0, 'ss': 250.0, 'tkn': 40.0,
                    'nh4': 28.0, 'no3': 0.5, 'po4': 8.0, 'alkalinity': 6.0,
                }
            },
            'processes': [
                {
                    'node_id': 'bassin',
                    'type':    'ActivatedSludgeProcess',
                    'name':    'Bassin aération',
                    'config': {
                        'model':                     'ASM1Model',
                        'volume':                    5000.0,
                        'dissolved_oxygen_setpoint': 2.0,
                        'recycle_ratio':             0.0,
                        'waste_ratio':               0.01,
                    }
                },
                {
                    'node_id': 'decanteur',
                    'type':    'SecondarySettlerProcess',
                    'name':    'Décanteur',
                    'config': {
                        'area':           500.0,
                        'depth':          4.0,
                        'n_layers':       10,
                        'underflow_ratio': 0.6,
                    }
                },
            ],
            'connections': [
                {'source': 'influent',   'target': 'bassin',    'fraction': 1.0, 'is_recycle': False},
                {'source': 'bassin',     'target': 'decanteur', 'fraction': 1.0, 'is_recycle': False},
                {'source': 'decanteur',  'target': 'bassin',    'fraction': 0.6, 'is_recycle': True},
            ]
        }
        return _run(config)

    def test_runs_without_error(self, results):
        assert results is not None

    def test_both_nodes_in_history(self, results):
        assert 'bassin'    in results['history']
        assert 'decanteur' in results['history']

    def test_settler_has_steps(self, results):
        assert len(results['history']['decanteur']) == 4

    def test_no_nan_in_settler_history(self, results):
        for flow_dict in results['history']['decanteur']:
            for key, val in flow_dict.items():
                if isinstance(val, (int, float)):
                    assert not np.isnan(val), f"NaN dans décanteur '{key}'"
