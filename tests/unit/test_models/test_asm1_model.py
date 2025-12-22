"""
Tests unitaires pour le modèle ASM1
"""
import pytest
import numpy as np

from unittest.mock import Mock, patch, MagicMock

from models.empyrical.asm1.model import ASM1Model
from models.empyrical.asm1.fraction import ASM1Fraction

class TestASM1Model:
    """Tests pour le modèle ASM1"""

    def test_model_initialization(self, asm1_model):
        """Test : initialisation du modèle"""
        assert asm1_model is not None
        assert hasattr(asm1_model, 'params')
        assert hasattr(asm1_model, 'stoichiometric_matrix')
        assert asm1_model.stoichiometric_matrix.shape == (8, 13)

    def test_component_indices(self, asm1_model):
        """Test : indices des composants"""

        expected_components = [
            'si', 'ss', 'xi', 'xs', 'xbh', 'xba', 'xp', 
            'so', 'sno', 'snh', 'snd', 'xnd', 'salk'
        ]
        assert len(asm1_model.COMPONENT_INDICES) == 13
        for comp in expected_components:
            assert comp in asm1_model.COMPONENT_INDICES
            assert 0 <= asm1_model.COMPONENT_INDICES[comp] < 13

    def test_compute_derivatives_shape(self, asm1_model):
        """Test : shape des dérivées"""
        concentrations = np.ones(13) * 100
        derivatives = asm1_model.compute_derivatives(concentrations)

        assert derivatives is not None
        assert derivatives.shape == (13,)
        assert isinstance(derivatives, np.ndarray)

    def test_compute_derivatives_zero_concentrations(self, asm1_model):
        """Test : dérivées avec concentrations nulles"""
        concentrations = np.zeros(13)
        derivatives = asm1_model.compute_derivatives(concentrations)

        assert not np.any(np.isnan(derivatives))
        assert not np.any(np.isinf(derivatives))

    def test_dict_to_concentrations(self, asm1_model):
        """Test : conversion dict -> array"""
        test_dict = {
            'so': 2.0,
            'xbh': 2500.0,
            'snh': 1.5
        }

        concentrations = asm1_model.dict_to_concentrations(test_dict)

        assert concentrations.shape == (13,)
        assert concentrations[asm1_model.COMPONENT_INDICES['so']] == 2.0
        assert concentrations[asm1_model.COMPONENT_INDICES['xbh']] == 2500.0
        assert concentrations[asm1_model.COMPONENT_INDICES['snh']] == 1.5

    def test_concentrations_to_dict(self, asm1_model):
        """Test: conversion array -> dict"""
        concentrations = np.ones(13)*10
        result_dict = asm1_model.concentrations_to_dict(concentrations)

        assert isinstance(result_dict, dict)
        assert len(result_dict) == 13
        assert all(v == 10.0 for v in result_dict.values())

    def test_roundtrip_conversion(self, asm1_model):
        """Test : conversion bidirectionnelle"""
        original = {
            'so': 2.0,
            'xbh': 2500.0,
            'xba': 150.0
        }

        array = asm1_model.dict_to_concentrations(original)
        recovered = asm1_model.concentrations_to_dict(array)

        for key in original:
            assert recovered[key] == original[key]

    @pytest.mark.parametrize('param_name,value', [
        ('mu_h', 10.0),
        ('k_s', 50.0),
        ('y_h', 0.8)
    ])
    def test_custom_parameters(self, param_name, value):
        """Test : paramètres personnalisés"""
        model = ASM1Model(params={param_name: value})
        assert model.params[param_name] == value

    @pytest.mark.parametrize('conc_level', [1, 10, 100, 1000])
    def test_numerical_stability(self, asm1_model, conc_level):
        """Test : stabilité numérique à différents niveaux"""
        concentrations = np.ones(13) * conc_level
        derivatives = asm1_model.compute_derivatives(concentrations)

        assert not np.any(np.isnan(derivatives))
        assert not np.any(np.isinf(derivatives))

class TestASM1WithMocks:
    """Tests utilisant des mocks pour isoler les dépendances"""

    @patch('models.empyrical.asm1.model.calculate_process_rates')
    def test_compute_derivatives_calls_kinetics(self, mock_kinetics):
        """Test : compute_derivatives appelle bien calculate_process_rates"""
        mock_kinetics.return_value = np.ones(8)

        model = ASM1Model()
        concentrations = np.ones(13)*100

        derivatives = model.compute_derivatives(concentrations)

        mock_kinetics.assert_called_once()
        assert derivatives is not None

    @patch('models.empyrical.asm1.model.build_stoichiometric_matrix')
    def test_initialization_builds_matrix(self, mock_build):
        """Test : la matrice stoichiométrique est construire à l'init"""
        mock_matrix = np.zeros((8, 13))
        mock_build.return_value = mock_matrix

        model = ASM1Model()

        mock_build.assert_called_once()
        assert model.stoichiometric_matrix is mock_matrix

@pytest.mark.parametrize('concentrations', [
    np.ones(13)*10,
    np.ones(13)*100,
    np.ones(13)*1000,
])
def test_stability_various_concentrations(asm1_model, concentrations):
    """Test : stabilité pour différentes concentrations"""
    derivatives = asm1_model.compute_derivatives(concentrations)

    assert not np.any(np.isnan(derivatives))
    assert not np.any(np.isinf(derivatives))

@pytest.mark.parametrize("cod,ss,expected_si_range", [
    (500, 250, (20,30)),
    (1000, 500, (40,60)),
    (200, 100, (8,12)),
])
def test_fractionation_ranges(cod, ss, expected_si_range):
    """Test : plages attendues pour le fractionnement"""
    components = ASM1Fraction.fractionate(cod=cod, tss=ss)
    si = components['si']
    assert expected_si_range[0] <= si <= expected_si_range[1]