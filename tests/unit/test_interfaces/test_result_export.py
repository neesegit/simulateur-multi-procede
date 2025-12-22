"""
Tests unitaires pour l'export de résultats
"""
import pytest
import json

from pathlib import Path
from unittest.mock import Mock, MagicMock, patch

from interfaces.result_exporter import ResultsExporter
from interfaces.metrics_exporter import MetricsExporter

class TestResultsExporter:
    """Tests pour ResultsExporter"""

    def test_export_to_csv(self, sample_simulation_results, tmp_path):
        """Test : export en CSV"""
        results = sample_simulation_results
        
        csv_files = ResultsExporter.export_to_csv(
            results,
            str(tmp_path)
        )

        assert isinstance(csv_files, dict)
        assert len(csv_files) > 0

        for node_id, path in csv_files.items():
            assert path.exists()
            assert path.suffix == '.csv'

    def test_export_to_json(self, sample_simulation_results, tmp_path):
        """Test : export en JSON"""
        results = sample_simulation_results
        output_path = tmp_path / "results.json"

        json_path = ResultsExporter.export_to_json(
            results,
            str(output_path)
        )
        
        assert json_path.exists()
        assert json_path.suffix == '.json'

        with open(json_path) as f:
            data = json.load(f)

        assert isinstance(data, dict)
        assert 'metadata' in data

    def test_export_summary(self, sample_simulation_results, tmp_path):
        """Test : export du résumé"""
        results = sample_simulation_results
        output_path = tmp_path / "summary.txt"

        summary_path = ResultsExporter.export_summary(
            results,
            str(output_path)
        )

        assert summary_path.exists()
        assert summary_path.suffix == '.txt'

        content = summary_path.read_text()
        assert 'Résumé' in content or 'simulation' in content

    def test_export_all(self, sample_simulation_results, tmp_path):
        """Test : export complet"""
        results = sample_simulation_results
        
        exported = ResultsExporter.export_all(
            results,
            str(tmp_path),
            name='test_sim'
        )

        assert isinstance(exported, dict)
        assert 'simulation_name' in exported
        assert 'base_directory' in exported
        assert 'files' in exported

        base_dir = Path(exported['base_directory'])
        assert base_dir.exists()
        assert base_dir.is_dir()

    def test_export_all_creates_subdirectories(self, sample_simulation_results, tmp_path):
        """Test : export_all crée les sous-répertoires"""
        results = sample_simulation_results

        exported = ResultsExporter.export_all(
            results,
            str(tmp_path),
            name='test_sim'
        )

        base_dir = Path(exported['base_directory'])
        csv_dir = base_dir / 'csv'

        assert csv_dir.exists()

    def test_export_empty_results(self, tmp_path):
        """Test : export de résultats vides"""
        results = {
            'metadata': {},
            'history': {},
            'statistics': {}
        }

        exported = ResultsExporter.export_all(
            results,
            str(tmp_path)
        )

        assert exported is not None

class TestMetricsExporter:
    """Tests pour MetricsExporter"""

    def test_export_performance_metrics(self, sample_simulation_results, tmp_path):
        """Test : export des métriques de performance"""
        results = sample_simulation_results

        json_path = MetricsExporter.export_performance_metrics(
            results,
            str(tmp_path)
        )

        assert json_path.exists()
        assert json_path.suffix == '.json'

        with open(json_path) as f:
            data = json.load(f)

        assert 'metadata' in data
        assert 'processes' in data

    def test_export_performance_csv(self, sample_simulation_results, tmp_path):
        """Test : export des métriques en CSV"""
        results = sample_simulation_results

        csv_files = MetricsExporter.export_performance_csv(
            results,
            str(tmp_path)
        )

        assert isinstance(csv_files, dict)

        for node_id, path in csv_files.items():
            assert path.exists()
            assert path.suffix == '.csv'

        def test_create_performance_report(self, sample_simulation_results, tmp_path):
            """Test : création du rapport de performance"""
            results = sample_simulation_results
            output_path = tmp_path / "report.txt"

            report_path = MetricsExporter.create_performance_report(
                results,
                str(output_path)
            )

            assert report_path.exists()

            content = report_path.read_text()
            assert 'Rapport de performance' in content or 'performance' in content.lower()

class TestExporters:
    
    @patch('interfaces.result_exporter.pd.DataFrame')
    @patch('interfaces.result_exporter.logger')
    def test_export_to_csv_logs(self, mock_logger, mock_df):
        """Test : export_to_csv log les messages"""
        results = {
            'history': {
                'proc1': [
                    {'timestamp': '2025-01-01', 'flowrate': 1000.0}
                ]
            }
        }

        mock_df_instance = MagicMock()
        mock_df.return_value = mock_df_instance

        ResultsExporter.export_to_csv(results, 'output')

        assert mock_logger.info.called or mock_logger.debug.called

    @patch('interfaces.result_exporter.json.dump')
    def test_export_to_json_writes_file(self, mock_dump):
        """Test : export_to_json écrit le fichier"""
        results = {'metadata': {}, 'history': {}}

        with patch('builtins.open', MagicMock()):
            ResultsExporter.export_to_json(results, 'output.json')

        mock_dump.assert_called_once()

class TestExportersEdgeCases:
    """Tests de cas limites"""

    def test_export_very_large_history(self, tmp_path):
        """Test : export d'un historique très large"""
        history = {
            'proc1': [
                {
                    'timestamp': f'2025-01-01T{i:02d}:00:00',
                    'flowrate': 1000.0 + i
                }
                for i in range(1000)
            ]
        }

        results = {
            'metadata': {},
            'history': history,
            'statistics': {}
        }

        csv_files = ResultsExporter.export_to_csv(results, str(tmp_path))

        assert len(csv_files) > 0

    def test_export_with_special_characters(self, tmp_path):
        """Test : export avec caractères spéciaux"""
        results = {
            'metadata': {'sim_name': 'test_sim_éàç'},
            'history': {},
            'statistics': {}
        }

        exported = ResultsExporter.export_all(
            results,
            str(tmp_path)
        )

        assert exported is not None

    def test_export_with_none_values(self, tmp_path):
        """Test : export avec valeurs None"""
        results = {
            'metadata': {'sim_name': None},
            'history': {
                'proc1': [
                    {'timestamp': '2025-01-01', 'flowrate': None}
                ]
            },
            'statistics': {}
        }

        exported = ResultsExporter.export_all(
            results,
            str(tmp_path)
        )

        assert exported is not None