"""
Tests end-to-end pour les simulations complètes
"""
import pytest
import json

from pathlib import Path

from core.orchestrator.simulation_orchestrator import SimulationOrchestrator
from core.process.process_factory import ProcessFactory
from interfaces.config import ConfigLoader
from interfaces import ResultsExporter

@pytest.mark.e2e
@pytest.mark.slow
class TestCompleteSimulation:
    """Tests de simulation complète"""

    def test_minimal_simulation(self, minimal_config):
        """Vérifie qu'une simulation minimale se termine correctement"""
        orchestrator = SimulationOrchestrator(minimal_config)

        processes = ProcessFactory.create_from_config(minimal_config)

        for process in processes:
            orchestrator.add_process(process)

        orchestrator.initialize()

        results = orchestrator.run()

        assert results is not None
        assert 'metadata' in results
        assert 'history' in results
        assert 'statistics' in results

    def test_simulation_with_results(self, minimal_config):
        """Vérifie qu'une simulation produit des résultats valides"""
        orchestrator = SimulationOrchestrator(minimal_config)
        processes = ProcessFactory.create_from_config(minimal_config)

        for process in processes:
            orchestrator.add_process(process)

        orchestrator.initialize()
        results = orchestrator.run()

        metadata = results['metadata']
        assert metadata['steps_completed'] > 0
        assert 'start_time' in metadata

        history = results['history']
        assert 'influent' in history
        assert 'test_as1' in history
        assert len(history['test_as1']) > 0

    def test_simulation_cod_removal(self, minimal_config):
        """Vérifie que la DCO diminue pendant la simulation"""
        orchestrator = SimulationOrchestrator(minimal_config)
        processes = ProcessFactory.create_from_config(minimal_config)

        for process in processes:
            orchestrator.add_process(process)

        orchestrator.initialize()

        # TODO