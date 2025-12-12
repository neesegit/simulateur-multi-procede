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
        assert 'so' in asm1_model.COMPONENT_INDICES
        assert 'xbh' in asm1_model.COMPONENT_INDICES
        assert len(asm1_model.COMPONENT_INDICES) == 13

    def test_compute_derivatives_shape(self, asm1_model):
        """Test : shape des dérivées"""
        concentrations = np.ones(13) * 100
        derivatives = asm1_model.compute_derivatives(concentrations)

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

class TestASM1Fraction:
    """Tests pour le fractionnement ASM1"""

    def test_basic_fractionation(self):
        """Test : fractionnement basique"""
        components = ASM1Fraction.fractionate(
            cod=500.0,
            ss=250.0,
            tkn=40.0,
            nh4=28.0,
            no3=0.5
        )
        assert isinstance(components, dict)
        assert 'si' in components
        assert 'xbh' in components
        assert components['snh'] == 28.0

    def test_fractionation_cod_balance(self):
        """Test : bilan de DCO"""
        cod_total = 500.0
        components = ASM1Fraction.fractionate(cod=cod_total, ss=250.0)

        cod_sum = sum(
            components.get(c, 0)
            for c in ['si', 'ss', 'xi', 'xs', 'xbh', 'xba']
        )

        assert abs(cod_sum - cod_total) < cod_total * 0.1

    def test_custom_ratios(self):
        """Test : ratios personnalisés"""
        custom_ratios = {
            'f_si_cod': 0.10,
            'f_ss_cod': 0.30
        }

        components = ASM1Fraction.fractionate(
            cod=500.0,
            ss=250.0,
            ratios=custom_ratios
        )

        assert abs(components['si'] - 50.0) < 5.0

    def test_negative_values_rejected(self):
        """Test : valeurs négatives rejetées"""
        components = ASM1Fraction.fractionate(
            cod=-100,
            ss=250.0
        )

        assert all(v >= 0 for v in components.values())

class TestASM1WithMocks:
    """Tests utilisant des mocks pour isoler les dépendances"""

    @patch('models.empyrical.asm1.kinetics.calculate_process_rates')
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

@pytest.mark.parametrize('Concentrations', [
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
    components = ASM1Fraction.fractionate(cod=cod, ss=ss)
    si = components['si']
    assert expected_si_range[0] <= si <= expected_si_range[1]