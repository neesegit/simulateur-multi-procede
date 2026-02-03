"""
Tests unitaires pour MetricsRegistry
"""
import pytest
from unittest.mock import MagicMock, patch

class TestMetricsRegistry:
    """Test pour le registre de métriques"""

    def test_singleton_pattern(self):
        """Test: MetricsRegistry implémente le pattern Singleton"""
        from core.registries.metrics_registry import MetricsRegistry

        instance1 = MetricsRegistry.get_instance()
        instance2 = MetricsRegistry.get_instance()

        assert instance1 is instance2
        assert id(instance1) == id(instance2)

    def test_register_calculator(self):
        """Test: Enregistrement d'un novueau calculateur de métrique"""
        from core.registries.metrics_registry import MetricsRegistry

        registry = MetricsRegistry.get_instance()

        mock_calculator = MagicMock()
        mock_calculator.calculate.return_value = 24.0

        registry.register('test_hrt', mock_calculator)

        assert registry.is_registered('test_hrt')
        calculator = registry.get_calculator('test_hrt')
        assert calculator == mock_calculator

    def test_register_duplicate_raises_error(self):
        """Test: Enregistrer une métrique existante lève une erreur"""
        from core.registries.metrics_registry import MetricsRegistry

        registry = MetricsRegistry.get_instance()

        mock_calc1 = MagicMock()
        mock_calc2 = MagicMock()

        registry.register('duplicate_metric', mock_calc1)

        with pytest.raises(ValueError, match='already registered'):
            registry.register('duplicate_metric', mock_calc2)

    def test_calculate_calls_correct_calculator(self):
        """Test: calculate appelle le bon calculateur"""
        from core.registries.metrics_registry import MetricsRegistry

        registry = MetricsRegistry.get_instance()

        mock_calculator = MagicMock()
        mock_calculator.calculate.return_value = 18.5

        registry.register('hrt_test', mock_calculator)

        state = {'volume': 1000.0}
        inputs = {'flow': MagicMock(flowrate=1500.0)}

        result = registry.calculate('hrt_test', state, inputs, {})

        mock_calculator.calculate.assert_called_once_with(state, inputs, {})

        assert result == 18.5

    def test_calculate_unregistered_metric_raises_error(self):
        """Test: Calculer une métrique non enregistrée lève une erreur"""
        from core.registries.metrics_registry import MetricsRegistry

        registry = MetricsRegistry.get_instance()

        with pytest.raises(ValueError, match='not registered'):
            registry.calculate('unknown_metric', {}, {}, {})

    def test_list_registered_metrics(self):
        """Test: Lister toutes les métriques enregistrées"""
        from core.registries.metrics_registry import MetricsRegistry

        registry = MetricsRegistry.get_instance()

        mock_calc1 = MagicMock()
        mock_calc2 = MagicMock()

        registry.register('metric_a', mock_calc1)
        registry.register('metric_b', mock_calc2)

        metrics = registry.list_registered_metrics()

        assert 'metric_a' in metrics
        assert 'metric_b' in metrics
        assert isinstance(metrics, list)

    def test_unregister_metric(self):
        """Test: désenregistrer une métrique"""
        from core.registries.metrics_registry import MetricsRegistry

        registry = MetricsRegistry.get_instance()

        mock_calculator = MagicMock()
        registry.register('temp_metric', mock_calculator)

        assert registry.is_registered('temp_metric')

        registry.unregister('temp_metric')

        assert not registry.is_registered('temp_metric')

    def test_calculate_with_exception_handling(self):
        """Test: Gestion des exceptions lors du calcul"""
        from core.registries.metrics_registry import MetricsRegistry

        registry = MetricsRegistry.get_instance()

        mock_calculator = MagicMock()
        mock_calculator.calculate.side_effect = ValueError('Invalid input')

        registry.register('error_metric', mock_calculator)

        with pytest.raises(ValueError, match='Invalid input'):
            registry.calculate('error_metric', {}, {}, {})

    def test_batch_calculate_multiple_metrics(self):
        """Test : Calculer plusieurs métriques en une fois"""
        from core.registries.metrics_registry import MetricsRegistry

        registry = MetricsRegistry.get_instance()

        mock_hrt = MagicMock()
        mock_hrt.calculate.return_value = 24.0

        mock_srt = MagicMock()
        mock_srt.calculate.return_value = 10.0

        mock_mlss = MagicMock()
        mock_mlss.calculate.return_value = 3500.0

        registry.register('hrt_batch', mock_hrt)
        registry.register('srt_batch', mock_srt)
        registry.register('mlss_batch', mock_mlss)

        metrics_to_calculate = ['hrt_batch', 'srt_batch', 'mlss_batch']
        context = {'volume': 1000.0,
                 'waste_ratio': 0.3}
        inputs = {'flow': MagicMock(flowrate=1500.0)}

        results = {}
        for metric in metrics_to_calculate:
            results[metric] = registry.calculate(metric, {"tss": 100}, inputs, context)

        assert results['hrt_batch'] == 24.0
        assert results['srt_batch'] == 10.0
        assert results['mlss_batch'] == 3500.0

class TestMetricsCalculators:
    """Test pour les calculateurs de métriques"""

    def test_hrt_calculator(self):
        """Test : Calculateur de HRT"""
        from core.registries.metrics_registry import MetricsRegistry

        registry = MetricsRegistry.get_instance()

        if not registry.is_registered('hrt'):
            mock_hrt = MagicMock()

            mock_hrt.calculate.return_value = 16.0
            registry.register('hrt', mock_hrt)

        context = {'volume': 1000.0}
        inputs = {'flow': MagicMock(flowrate=1500.0)}

        hrt = registry.calculate('hrt', {}, inputs, context)

        assert isinstance(hrt, dict)
        for (key, value) in hrt.items():
            assert value > 0

    def test_srt_calculator(self):
        """Test : Calculateur de SRT"""
        from core.registries.metrics_registry import MetricsRegistry

        registry = MetricsRegistry.get_instance()

        if not registry.is_registered('srt'):
            mock_srt = MagicMock()
            mock_srt.calculate.return_value = 10.0
            registry.register('srt', mock_srt)

        context = {
            'volume': 1000.0,
            'waste_ratio': 0.01
        }
        inputs = {'flowrate': 1500.0}
        components = {'tss': 3000.0}

        srt = registry.calculate('srt', components, inputs, context)

        assert isinstance(srt, dict)
        for (key, value) in srt.items():
            assert value > 0

    def test_svi_calculator(self):
        """Test : Calculateur de SVI"""
        from core.registries.metrics_registry import MetricsRegistry

        registry = MetricsRegistry.get_instance()

        if not registry.is_registered('svi'):
            mock_svi = MagicMock()
            mock_svi.calculate.return_value = 120.0
            registry.register('svi', mock_svi)

        components = {'tss': 3000.0}
        context = {'volume': 1000.0}

        svi = registry.calculate('svi', components, {}, context)

        assert isinstance(svi, dict)
        for (key, value) in svi.items():
            assert value > 0

    def test_energy_calculator(self):
        """Test : Calculateur de consommation énergétique"""
        from core.registries.metrics_registry import MetricsRegistry

        registry = MetricsRegistry.get_instance()

        if not registry.is_registered('energy'):
            mock_energy = MagicMock()
            mock_energy.calculate.return_value = 0.35
            registry.register('energy', mock_energy)

        inputs = {
            'cod_in': 500.0,
            'flowrate': 200.0
        }
        components = {
            'cod': 200.0
        }
        context = {'dt': 0.1}

        energy = registry.calculate('energy', components, inputs, context)

        assert isinstance(energy, dict)
        for (key, value) in energy.items():
            assert value > 0

class TestCompositionCalculators:
    """Test pour les calculateurs composites"""

    def test_composite_calculator_(self):
        """Test : Calculateur composite"""
        from core.registries.metrics_registry import (
            MetricsRegistry,
            create_composite_calculator,
            CompositeMetricCalculator
        )

        registry = MetricsRegistry.get_instance()

        if registry.is_registered('cod'):
            registry.unregister('cod')

        mock_model_def = MagicMock()
        mock_model_def.get_metrics_dict.return_value = {
            'cod': ['si', 'ss', 'xi', 'xs']
        }

        composite_calculator = create_composite_calculator(mock_model_def, 'cod')

        assert isinstance(composite_calculator, CompositeMetricCalculator)

        registry.register('cod', composite_calculator)

        components = {
            'si': 25.0,
            'ss': 25.0,
            'xi': 100.0,
            'xs': 100.0
        }

        result = registry.calculate('cod', components, {}, {})

        assert result == {'value': 250.0}