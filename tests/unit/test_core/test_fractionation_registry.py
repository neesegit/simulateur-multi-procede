"""
Tests unitaires pour FractionationRegistry
"""
import pytest
from unittest.mock import MagicMock, patch

class TestFractionationRegistry:
    """Tests pour le registre de fractionnement"""

    def test_singleton_pattern(self):
        """Test: FractionationRegistry implémnete le pattern singleton"""
        from core.registries.fractionation.registry import FractionationRegistry

        instance1 = FractionationRegistry.get_instance()
        instance2 = FractionationRegistry.get_instance()

        assert instance1 is instance2
        assert id(instance1) == id(instance2)

    def test_register_fractionator(self):
        """Test: enregistrement d'un nouveau fractionneur"""
        from core.registries.fractionation.registry import FractionationRegistry

        registry = FractionationRegistry.get_instance()

        mock_fractionator = MagicMock()
        mock_fractionator.fractionate.return_value = {'si': 10.0, 'ss': 50.0}

        registry.register('TEST_MODEL', mock_fractionator)

        assert registry.get_strategy('TEST_MODEL') == mock_fractionator

    def test_register_duplicate_raises_error(self):
        """Test: Enregistrer un modèle existant lève une erreur"""
        from core.registries.fractionation.registry import FractionationRegistry

        registry = FractionationRegistry.get_instance()

        mock_fractionator1 = MagicMock()
        mock_fractionator2 = MagicMock()

        registry.register('DUPLICATE_TEST', mock_fractionator1)

        with pytest.raises(ValueError, match="already registered"):
            registry.register('DUPLICATE_TEST', mock_fractionator2)

    def test_fractionate_calls_correct_fractionator(self):
        """Test: fractionate appelle le bon fractionneur"""
        from core.registries.fractionation.registry import FractionationRegistry

        registry = FractionationRegistry.get_instance()

        mock_fractionator = MagicMock()
        mock_fractionator.fractionate.return_value = {
            'si': 25.0, 'ss': 100.0, 'xi': 50.0, 'xs': 200.0,
            'so': 2.0, 'snh': 25.0, 'sno': 5.0
        }

        registry.register('ASM1_TEST', mock_fractionator)

        result = registry.fractionate(
            model_type='ASM1_TEST',
            cod=500.0,
            tss=200.0,
            tkn=40.0,
            nh4=25.0,
            no3=5.0,
            po4=8.0,
            alkalinity=200.0
        )

        mock_fractionator.fractionate.assert_called_once_with(
            cod=500.0,
            tss=200.0,
            tkn=40.0,
            nh4=25.0,
            no3=5.0,
            po4=8.0,
            alkalinity=200.0
        )

        assert result['si'] == 25.0
        assert result['ss'] == 100.0

    def test_fractionate_unregistered_model_raises_error(self):
        """Test: Fractionner un modèle non enregistré lève une erreur"""
        from core.registries.fractionation.registry import FractionationRegistry

        registry = FractionationRegistry.get_instance()

        with pytest.raises(ValueError, match="not registered"):
            registry.fractionate(
                model_type='UNKNOWN_MODEL',
                cod=500.0
            )

    def test_list_registered_models(self):
        """Test: Lister tous les modèles enregistrés"""
        from core.registries.fractionation.registry import FractionationRegistry

        registry = FractionationRegistry.get_instance()

        mock_frac1 = MagicMock()
        mock_frac2 = MagicMock()

        registry.register('MODEL_A', mock_frac1)
        registry.register('MODEL_B', mock_frac2)

        models = registry.list_registered_models()

        assert 'MODEL_A' in models
        assert 'MODEL_B' in models
        assert isinstance(models, list)

    def test_unregister_model(self):
        """Test : Désenregistrer un modèle"""
        from core.registries.fractionation.registry import FractionationRegistry

        registry = FractionationRegistry.get_instance()

        mock_fractionator = MagicMock()
        registry.register('TEMP_MODEL', mock_fractionator)

        assert registry.is_registered('TEMP_MODEL')

        registry.unregister('TEMP_MODEL')

        assert not registry.is_registered('TEMP_MODEL')

    def test_fractionate_with_partial_parameters(self):
        """Test: fractionner avec seulement certains paramètres fournis"""
        from core.registries.fractionation.registry import FractionationRegistry

        registry = FractionationRegistry.get_instance()

        mock_fractionator = MagicMock()
        mock_fractionator.fractionate.return_value = {'si': 20.0, 'ss': 80.0}

        registry.register('PARTIAL_TEST', mock_fractionator)

        result = registry.fractionate(
            model_type='PARTIAL_TEST',
            cod=400.0,
            tss=150.0
        )

        mock_fractionator.fractionate.assert_called_once()
        call_kwargs = mock_fractionator.fractionate.call_args.kwargs

        assert call_kwargs['cod'] == 400.0
        assert call_kwargs['tss'] == 150.0
        assert call_kwargs.get('tkn') == 0.0
        assert call_kwargs.get('nh4') == 0.0
