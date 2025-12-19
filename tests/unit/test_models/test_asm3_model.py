"""
Tests unitaires pour le modèle ASM3
"""
import pytest
import numpy as np

from unittest.mock import Mock, patch, MagicMock

from models.empyrical.asm3.model import ASM3Model

class TestASM3Model:
    """Tests unitaires pour ASM3Model"""

    def test_model_initialization(self, asm3_model):
        """Test : initialisation du modèle"""
        assert asm3_model is not None
        assert hasattr(asm3_model, 'params')
        assert hasattr(asm3_model, 'stoichiometric_matrix')
        assert asm3_model.stoichiometric_matrix.shape == (12, 13)

    def test_component_indices(self, asm3_model):
        """Test : composants asm3"""

        components = [
            'so2', 'si', 'ss', 'snh4', 'snox', 'xh', 'xsto', 'xa'
        ]
        assert len(asm3_model.COMPONENT_INDICES) == 13
        for comp in components:
            assert comp in asm3_model.COMPONENT_INDICES

    def test_compute_derivatives_shape(self, asm3_model):
        """Test : shape des dérivées"""
        concentrations = np.ones(13) * 100
        derivatives = asm3_model.compute_derivatives(concentrations)

        assert derivatives is not None
        assert derivatives.shape == (13,)
        assert isinstance(derivatives, np.ndarray)

    def test_compute_derivatives_zero_concentrations(self, asm3_model):
        """Test : dérivées avec concentrations nulles"""
        concentrations = np.zeros(13)
        derivatives = asm3_model.compute_derivatives(concentrations)

        assert not np.any(np.isnan(derivatives))
        assert not np.any(np.isinf(derivatives))

    def test_dict_to_concentrations(self, asm3_model):
        """Test : conversion dict -> array"""
        test_dict = {
            'so2': 2.0,
            'snox': 2500.0,
            'xsto': 1.5
        }

        concentrations = asm3_model.dict_to_concentrations(test_dict)

        assert concentrations.shape == (19,)
        assert concentrations[asm3_model.COMPONENT_INDICES['so2']] == 2.0
        assert concentrations[asm3_model.COMPONENT_INDICES['snox']] == 2500.0
        assert concentrations[asm3_model.COMPONENT_INDICES['xsto']] == 1.5

    def test_concentrations_to_dict(self, asm3_model):
        """Test: conversion array -> dict"""
        concentrations = np.ones(13)*10
        result_dict = asm3_model.concentrations_to_dict(concentrations)

        assert isinstance(result_dict, dict)
        assert len(result_dict) == 13
        assert all(v == 10.0 for v in result_dict.values())

    def test_roundtrip_conversion(self, asm3_model):
        """Test : conversion bidirectionnelle"""
        original = {
            'so2': 2.0,
            'snox': 2500.0,
            'xsto': 1.5
        }

        array = asm3_model.dict_to_concentrations(original)
        recovered = asm3_model.concentrations_to_dict(array)

        for key in original:
            assert recovered[key] == original[key]

    @pytest.mark.parametrize('param_name,value', [
        ('mu_h', 10.0),
        ('k_s', 50.0),
        ('y_h_o2', 0.8)
    ])
    def test_custom_parameters(self, param_name, value):
        """Test : paramètres personnalisés"""
        model = ASM3Model(params={param_name: value})
        assert model.params[param_name] == value

    @pytest.mark.parametrize('conc_level', [1, 10, 100, 1000])
    def test_numerical_stability(self, asm3_model, conc_level):
        """Test : stabilité numérique à différents niveaux"""
        concentrations = np.ones(13) * conc_level
        derivatives = asm3_model.compute_derivatives(concentrations)

        assert not np.any(np.isnan(derivatives))
        assert not np.any(np.isinf(derivatives))

class Testasm3dWithMocks:
    """Tests utilisant des mocks pour isoler les dépendances"""

    @patch('models.empyrical.asm1.kinetics.calculate_process_rates')
    def test_compute_derivatives_calls_kinetics(self, mock_kinetics):
        """Test : compute_derivatives appelle bien calculate_process_rates"""
        mock_kinetics.return_value = np.ones(12)

        model = ASM3Model()
        concentrations = np.ones(13)*100

        derivatives = model.compute_derivatives(concentrations)

        mock_kinetics.assert_called_once()
        assert derivatives is not None

    @patch('models.empyrical.asm1.model.build_stoichiometric_matrix')
    def test_initialization_builds_matrix(self, mock_build):
        """Test : la matrice stoichiométrique est construire à l'init"""
        mock_matrix = np.zeros((12, 13))
        mock_build.return_value = mock_matrix

        model = ASM3Model()

        mock_build.assert_called_once()
        assert model.stoichiometric_matrix is mock_matrix

@pytest.mark.parametrize('Concentrations', [
    np.ones(19)*10,
    np.ones(19)*100,
    np.ones(19)*1000,
])
def test_stability_various_concentrations(asm3_model, concentrations):
    """Test : stabilité pour différentes concentrations"""
    derivatives = asm3_model.compute_derivatives(concentrations)

    assert not np.any(np.isnan(derivatives))
    assert not np.any(np.isinf(derivatives))