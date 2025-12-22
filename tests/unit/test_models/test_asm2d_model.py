"""
Tests unitaires pour le modèle ASM2d
"""
import pytest
import numpy as np

from unittest.mock import Mock, patch, MagicMock

from models.empyrical.asm2d.model import ASM2dModel

class TestASM2dModel:
    """Tests unitaires pour ASM2dModel"""

    def test_model_initialization(self, asm2_model):
        """Test : initialisation du modèle"""
        assert asm2_model is not None
        assert hasattr(asm2_model, 'params')
        assert hasattr(asm2_model, 'stoichiometric_matrix')
        assert asm2_model.stoichiometric_matrix.shape == (21,19)

    def test_component_indices(self, asm2_model):
        """Test : composants spécifiques ASM2d"""

        components = [
            'so2', 'sf', 'sa', 'snh4', 'sno3', 'spo4',
            'xh', 'xpao', 'xpp', 'xpha', 'xaut'
        ]
        assert len(asm2_model.COMPONENT_INDICES) == 19
        for comp in components:
            assert comp in asm2_model.COMPONENT_INDICES

    def test_compute_derivatives_shape(self, asm2_model):
        """Test : shape des dérivées"""
        concentrations = np.ones(19) * 100
        derivatives = asm2_model.compute_derivatives(concentrations)

        assert derivatives is not None
        assert derivatives.shape == (19,)
        assert isinstance(derivatives, np.ndarray)

    def test_compute_derivatives_zero_concentrations(self, asm2_model):
        """Test : dérivées avec concentrations nulles"""
        concentrations = np.zeros(19)
        derivatives = asm2_model.compute_derivatives(concentrations)

        assert not np.any(np.isnan(derivatives))
        assert not np.any(np.isinf(derivatives))

    def test_dict_to_concentrations(self, asm2_model):
        """Test : conversion dict -> array"""
        test_dict = {
            'so2': 2.0,
            'xpp': 2500.0,
            'snh4': 1.5
        }

        concentrations = asm2_model.dict_to_concentrations(test_dict)

        assert concentrations.shape == (19,)
        assert concentrations[asm2_model.COMPONENT_INDICES['so2']] == 2.0
        assert concentrations[asm2_model.COMPONENT_INDICES['xpp']] == 2500.0
        assert concentrations[asm2_model.COMPONENT_INDICES['snh4']] == 1.5

    def test_concentrations_to_dict(self, asm2_model):
        """Test: conversion array -> dict"""
        concentrations = np.ones(19)*10
        result_dict = asm2_model.concentrations_to_dict(concentrations)

        assert isinstance(result_dict, dict)
        assert len(result_dict) == 19
        assert all(v == 10.0 for v in result_dict.values())

    def test_roundtrip_conversion(self, asm2_model):
        """Test : conversion bidirectionnelle"""
        original = {
            'so2': 2.0,
            'xpp': 2500.0,
            'snh4': 1.5
        }

        array = asm2_model.dict_to_concentrations(original)
        recovered = asm2_model.concentrations_to_dict(array)

        for key in original:
            assert recovered[key] == original[key]

    @pytest.mark.parametrize('param_name,value', [
        ('mu_h', 10.0),
        ('k_ps', 50.0),
        ('y_h', 0.8)
    ])
    def test_custom_parameters(self, param_name, value):
        """Test : paramètres personnalisés"""
        model = ASM2dModel(params={param_name: value})
        assert model.params[param_name] == value

    @pytest.mark.parametrize('conc_level', [1, 10, 100, 1000])
    def test_numerical_stability(self, asm2_model, conc_level):
        """Test : stabilité numérique à différents niveaux"""
        concentrations = np.ones(19) * conc_level
        derivatives = asm2_model.compute_derivatives(concentrations)

        assert not np.any(np.isnan(derivatives))
        assert not np.any(np.isinf(derivatives))

class TestASM2dWithMocks:
    """Tests utilisant des mocks pour isoler les dépendances"""

    @patch('models.empyrical.asm2d.model.calculate_process_rates')
    def test_compute_derivatives_calls_kinetics(self, mock_kinetics):
        """Test : compute_derivatives appelle bien calculate_process_rates"""
        mock_kinetics.return_value = np.ones(21)

        model = ASM2dModel()
        concentrations = np.ones(19)*100

        derivatives = model.compute_derivatives(concentrations)

        mock_kinetics.assert_called_once()
        assert derivatives is not None

    @patch('models.empyrical.asm2d.model.build_stoichiometric_matrix')
    def test_initialization_builds_matrix(self, mock_build):
        """Test : la matrice stoichiométrique est construire à l'init"""
        mock_matrix = np.zeros((21, 19))
        mock_build.return_value = mock_matrix

        model = ASM2dModel()

        mock_build.assert_called_once()
        assert model.stoichiometric_matrix is mock_matrix

@pytest.mark.parametrize('concentrations', [
    np.ones(19)*10,
    np.ones(19)*100,
    np.ones(19)*1000,
])
def test_stability_various_concentrations(asm2_model, concentrations):
    """Test : stabilité pour différentes concentrations"""
    derivatives = asm2_model.compute_derivatives(concentrations)

    assert not np.any(np.isnan(derivatives))
    assert not np.any(np.isinf(derivatives))