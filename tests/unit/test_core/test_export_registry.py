"""
Tests unitaires pour ExportRegistry
"""
import pytest
import json
from pathlib import Path
from unittest.mock import Mock, MagicMock, patch, mock_open
import pandas as pd

from core.registries.export_registry import (
    ExportRegistry,
    ExportStrategy,
    CSVExportStrategy,
    JSONExportStrategy,
    ExcelExportStrategy,
    ParquetExportStrategy
)

class TestExportStrategy:
    """Tests pour l'interface Export Strategy"""

    def test_export_strategy_is_abstract(self):
        """Test : ExportStrategy est une classe abstraite"""
        with pytest.raises(TypeError):
            ExportStrategy() # type: ignore

class TestCSVExportStrategy:
    """Tests pour CSVExportStrategy"""

    def test_initialization(self):
        """Test : initialisation"""
        strategy = CSVExportStrategy()

        assert strategy is not None
        assert strategy.format_name == "CSV"
        assert strategy.file_extension == ".csv"

    def test_supports_node(self):
        """Test : supporte tous les types de noeuds"""
        strategy = CSVExportStrategy()

        assert strategy.supports_node('ActivatedSludgeProcess')
        assert strategy.supports_node('SecondarySettler')
        assert strategy.supports_node('AnyNodeType')

    def test_export_creates_csv(self, tmp_path):
        """Test : export crée un fichier CSV"""
        strategy = CSVExportStrategy()

        results = {
            'history': {
                'proc1': [
                    {
                        'timestampe': '2025-01-01T00:00:00',
                        'flowrate': 1000.0,
                        'temperature': 20.0,
                        'components': {'cod': 50.0, 'tss': 2000.0}
                    },
                    {
                        'timestampe': '2025-01-01T00:10:00',
                        'flowrate': 1100.0,
                        'temperature': 21.0,
                        'components': {'cod': 45.0, 'tss': 2100.0}
                    }
                ]
            }
        }

        filepath = strategy.export(results, tmp_path, node_id='proc1')

        assert filepath.exists()
        assert filepath.suffix == '.csv'
        assert 'proc1' in filepath.name

        df = pd.read_csv(filepath)
        assert len(df) == 2
        assert 'timestamp' in df.columns
        assert 'flowrate' in df.columns
        assert 'cod' in df.columns
        assert 'tss' in df.columns

    def test_export_raises_error_if_node_not_found(self, tmp_path):
        """Test : lève une erreur si le noeud n'existe pas"""
        strategy = CSVExportStrategy()

        results = {
            'history': {
                'proc1': []
            }
        }

        with pytest.raises(ValueError, match='not found'):
            strategy.export(results, tmp_path, node_id='nonexistent')

    def test_export_handles_empty_components(self, tmp_path):
        """Test : gère les composants vides"""
        strategy = CSVExportStrategy()

        results = {
            'history': {
                'proc1': [
                    {
                        'timestampe': '2025-01-01T00:00:00',
                        'flowrate': 1000.0,
                        'temperature': 20.0,
                        'components': {}
                    }
                ]
            }
        }

        filepath = strategy.export(results, tmp_path, node_id='proc1')

        assert filepath.exists()
        df = pd.read_csv(filepath)
        assert 'timestamp' in df.columns
        assert 'flowrate' in df.columns

class TestJSONExportStrategy:
    """Tests pour JSONExportStrategy"""

    def test_initialization(self):
        """Test : initialisation"""
        strategy = JSONExportStrategy()

        assert strategy.format_name == 'JSON'
        assert strategy.file_extension == '.json'

    def test_export_creates_json(self, tmp_path):
        """Test : export crée un fichier JSON"""
        strategy = JSONExportStrategy()

        results = {
            'metadata': {
                'sim_name': 'test_sim',
                'start_time': '2025-01-01T00:00:00'
            },
            'history': {
                'proc1': [
                    {'timestamp': '2025-01-01', 'flowrate': 1000.0}
                ]
            }
        }

        filepath = strategy.export(results, tmp_path, name='test_simulation')

        assert filepath.exists()
        assert filepath.suffix == '.json'
        assert 'test_simulation' in filepath.name

        with open(filepath) as f:
            data = json.load(f)

        assert 'metadata' in data
        assert 'history' in data
        assert data['metadata']['sim_name'] == 'test_sim'

    def test_export_handles_datatime_objects(self, tmp_path):
        """Test : gère les objets datetime"""
        from datetime import datetime

        strategy = JSONExportStrategy()

        results = {
            'metadata': {
                'timestamp': datetime(2025, 1, 1, 12, 0, 0)
            },
            'history': {}
        }

        filepath = strategy.export(results, tmp_path)

        assert filepath.exists()

        with open(filepath) as f:
            data = json.load(f)

        assert 'metadata' in data

class TestExportRegistry:
    """Tests pour ExportRegistry"""

    def test_singleton_pattern(self):
        """Test : implémente le pattern singleton"""
        instance1 = ExportRegistry.get_instance()
        instance2 = ExportRegistry.get_instance()

        assert instance1 is instance2
        assert id(instance1) == id(instance2)