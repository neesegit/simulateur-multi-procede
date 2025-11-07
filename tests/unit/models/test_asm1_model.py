"""
Tests unitaire pour le modèle ASM1
"""
import pytest
import numpy as np

from models.asm1.model import ASM1Model
from models.asm1.fraction import ASM1Fraction

@pytest.mark.unit
@pytest.mark.models
class TestASM1Model:
    """Tests du modèle ASM1"""

    def test_model_initialization(self):
        """Vérifie l'initialisation du modèle"""
        model = ASM1Model()

        assert model is not None
        assert hasattr(model, 'params')
        assert hasattr(model, 'stoichiometric_matrix')
        assert model.stoichiometric_matrix.shape == (8,13)

    def test_default_parameters(self):
        """Vérifie que les paramètres par défaut sont valides"""
        model = ASM1Model()

        assert model.params['mu_h'] > 0
        assert model.params['y_h'] > 0
        assert model.params['y_h'] < 1
        assert model.params['k_s'] > 0

    def test_custom_parameters(self):
        """Vérifie l'utilisation de paramètres personnalisés"""
        custom_params = {'mu_h': 7.0, 'k_s': 25.0}
        model = ASM1Model(params= custom_params)

        assert model.params['mu_h'] == 7.0
        assert model.params['k_s'] == 25.0
        assert model.params['y_h'] == model.DEFAULT_PARAMS['y_h']

    def test_component_names(self):
        """Vérifie que tous les composants sont présents"""
        model = ASM1Model()
        names = model.get_component_names()

        expected = ['si', 'ss', 'xi', 'xs', 'xbh', 'xba', 'xp', 'so', 'sno', 'snh', 'snd', 'xnd', 'salk']
        assert len(names) == 13
        assert set(names) == set(expected)

    def test_concentrations_to_dict(self, sample_asm1_components):
        """Vérifie la conversion concentrations -> dict"""
        model = ASM1Model()

        c = model.dict_to_concentrations(sample_asm1_components)
        result = model.concentrations_to_dict(c)

        for key, value in sample_asm1_components.items():
            assert abs(result[key] - value) < 1e-6

    def test_dict_to_concentration(self, sample_asm1_components):
        """Vérifie la conversion dict -> concentrations"""
        model = ASM1Model()
        c = model.dict_to_concentrations(sample_asm1_components)

        assert isinstance(c, np.ndarray)
        assert c.shape == (13,)
        assert np.all(c >= 0)

    def test_compute_derivatives_shape(self, sample_asm1_components):
        """Vérifie que compute_derivatives retourne la bonne forme"""
        model= ASM1Model()
        c = model.dict_to_concentrations(sample_asm1_components)

        derivatives = model.compute_derivatives(c)

        assert isinstance(derivatives, np.ndarray)
        assert derivatives.shape == (13,)
        assert np.all(np.isfinite(derivatives))

    def test_compute_derivatives_realistic(self, sample_asm1_components):
        """Vérifie que les dérivées sont réalistes"""
        model = ASM1Model()
        c = model.dict_to_concentrations(sample_asm1_components)

        derivatives = model.compute_derivatives(c)

        xbh_idx = model.COMPONENT_INDICES['xbh']
        assert derivatives[xbh_idx] > 0, 'La biomasse devrait croître'

        ss_idx = model.COMPONENT_INDICES['ss']
        assert derivatives[ss_idx] < 0, 'Le substrat devrait diminuer'

    def test_step_no_negative_concentrations(self, sample_asm1_components):
        """Vérifie qu'un pas de simulation ne produit pas de concentrations négatives"""
        model = ASM1Model()
        c = model.dict_to_concentrations(sample_asm1_components)

        dt = 0.1 # 0.1 jour
        c_next = model.step(c, dt)

        assert np.all(c_next >= 0), 'Concentration négatives détectées'

    def test_step_with_oxygen_setpoint(self, sample_asm1_components):
        """Vérifie que la consigne d'oxygène est respectée"""
        model = ASM1Model()
        c = model.dict_to_concentrations(sample_asm1_components)

        so_setpoint = 3.0
        c_next = model.step(c, dt=0.1, so_setpoint=so_setpoint)

        so_idx = model.COMPONENT_INDICES['so']
        assert abs(c_next[so_idx] - so_setpoint) < 1e-6

    def test_multiple_steps_stability(self, sample_asm1_components):
        """Vérifie la stabilité sur plusieurs pas de temps"""
        model = ASM1Model()
        c = model.dict_to_concentrations(sample_asm1_components)

        for _ in range(100):
            c = model.step(c, dt=0.01, so_setpoint=2.0)

            assert np.all(c >= 0)
            assert np.all(np.isfinite(c))
    
    def test_steady_state_convergence(self, sample_asm1_components):
        """Vérifie que le modèle converge vers un état stable"""
        model = ASM1Model()
        c = model.dict_to_concentrations(sample_asm1_components)

        for _ in range(1000):
            c = model.step(c, dt= 0.1, so_setpoint=2.0)

        derivatives = model.compute_derivatives(c)
        max_derivative = np.max(np.abs(derivatives))

        assert max_derivative < 100, 'Le modèle ne converge pas vers un état stable'

@pytest.mark.unit
@pytest.mark.models
class TestASM1Fraction:
    """Tests du fractionnement ASM1"""

    def test_fractionate_basic(self):
        """Vérifie le fractionnement de base"""
        result = ASM1Fraction.fractionate(
            cod=500.0,
            ss=250.0,
            tkn=40.0,
            nh4=28.0
        )

        assert isinstance(result, dict)
        assert len(result) > 0
        assert 'si' in result
        assert 'ss' in result
        assert 'xbh' in result
    
    def test_fractionate_cod_conservation(self):
        """Vérifie que la DCO est conservée"""
        cod_total = 500.0
        result = ASM1Fraction.fractionate(cod=cod_total)

        cod_fractions = sum(result[k] for k in ['si', 'ss', 'xi', 'xs', 'xbh', 'xba'])

        assert abs(cod_fractions - cod_total) / cod_total < 0.1

    def test_fractionate_nitrogen_conservation(self):
        """Vérifie que l'azote est conservé"""
        tkn = 40.0
        nh4 = 28.0

        result = ASM1Fraction.fractionate(cod=500.0, tkn=tkn, nh4=nh4)

        n_total = result['snh'] + result['snd'] + result['xnd']

        assert abs(n_total - tkn) / tkn < 0.15

    def test_fractionate_no_negative_values(self):
        """Vérifie qu'il n'y a pas de valeurs négatives"""
        result = ASM1Fraction.fractionate(
            cod=500.0,
            ss=250.0,
            tkn=40.0,
            nh4=28.0,
            no3=0.5
        )

        for key, value in result.items():
            assert value >= 0, f"Valeur négative pour {key}: {value}"

    def test_fractionate_custom_ratios(self):
        """Vérifie l'utilisation de ratios personnalisés"""
        custom_ratios = {
            'f_si_cod': 0.10, # Plus d'inertes
        }

        result = ASM1Fraction.fractionate(
            cod=500.0,
            ratios=custom_ratios
        )

        expected_si = 500.0*0.10
        assert abs(result['si'] - expected_si) < 1.0

    def test_fractionate_with_alkalinity(self):
        """Vérifie le traitement de l'alcalinité"""
        alkalinity = 7.0
        result = ASM1Fraction.fractionate(
            cod=500.0,
            alkalinity=alkalinity
        )

        assert 'salk' in result
        assert result['salk'] == alkalinity

    def test_fractionate_without_alkalinity(self):
        """Vérifie l'estimation de l'alcalinité"""
        result = ASM1Fraction.fractionate(
            cod = 500.0,
            tkn=40.0
        )

        assert 'salk' in result
        assert result['salk'] > 0