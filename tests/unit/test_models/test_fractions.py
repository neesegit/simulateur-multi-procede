"""
Tests unitaires pour le fractionnement ASM
"""
import pytest
import numpy as np

from unittest.mock import patch

from models.empyrical.asm1.fraction import ASM1Fraction
from models.empyrical.asm2d.fraction import ASM2DFraction
from models.empyrical.asm3.fraction import ASM3Fraction

class TestASM1Fraction:
    """Tests pour ASM1Fraction"""

    def test_basic_fractionation(self):
        """Test : fractionnement basique"""
        components = ASM1Fraction.fractionate(
            cod=500.0,
            tss=250.0,
            tkn=40.0,
            nh4=28.0,
            no3=0.5
        )

        assert isinstance(components, dict)
        assert len(components) > 0

    def test_all_components_present(self):
        """Test : tous les composants ASM1 sont générés"""
        components = ASM1Fraction.fractionate(
            cod=500.0,
            tss=250.0,
            tkn=40.0,
            nh4=28.0
        )

        expected = [
            'si', 'ss', 'xi', 'xbh', 'xba', 'xp',
            'snh', 'sno', 'snd', 'xnd', 'salk'
        ]

        for comp in expected:
            assert comp in components

    def test_cod_balance(self):
        """Test : bilan de DCO conservé"""
        cod_total = 500.0

        components = ASM1Fraction.fractionate(
            cod=cod_total,
            tss=250.0,
            tkn=40.0
        )

        cod_components = ['si', 'ss', 'xi', 'xs', 'xbh', 'xba']
        cod_sum = sum(components.get(c, 0) for c in cod_components)

        assert abs(cod_sum - cod_total) < cod_total * 0.10

    def test_nitrogen_balance(self):
        """Test : bilan d'azote"""
        tkn = 40.0
        nh4 = 28.0

        components = ASM1Fraction.fractionate(
            cod=500.0,
            tss=250.0,
            tkn=tkn,
            nh4=nh4,
            no3=0.5
        )

        assert components['snh'] == nh4

        n_organic = components.get('snd', 0) + components.get('xnd', 0)
        assert n_organic > 0
    
    def test_custom_ratios(self):
        """Test : ratios personnalisés"""
        custom_ratios = {
            'f_si': 0.10
        }

        components = ASM1Fraction.fractionate(
            cod=500.0,
            ratios=custom_ratios
        )

        assert 45 <= components['si'] <= 55
        assert 400 <= components['ss'] <= 500

    def test_zero_values(self):
        """Test: valeurs nulles"""
        components = ASM1Fraction.fractionate(
            cod=0.0
        )

        assert components is not None
        assert all(v >= 0 for v in components.values())

    def test_high_load(self):
        """Test : charge élevée"""
        components = ASM1Fraction.fractionate(
            cod=2000.0,
            tss=1000.0,
            tkn=100.0,
            nh4=70.0
        )

        assert components is not None
        assert components['xbh'] > 0

    def test_alkalinity_estimation(self):
        """Test : estimation de l'alcalinité"""
        comp1 = ASM1Fraction.fractionate(
            cod=500.0,
            tss=250.0,
            tkn=40.0,
            alkalinity=None
        )

        assert 'salk' in comp1
        assert comp1['salk'] > 0

        comp2 = ASM1Fraction.fractionate(
            cod=500.0,
            tss=250.0,
            tkn=40.0,
            alkalinity=8.0
        )

        assert 'salk' in comp2
        assert comp2['salk'] == 8.0

    @pytest.mark.parametrize('cod, ss, expected_range', [
        (100,50,(3, 7)),
        (500,250, (20, 30)),
        (1000, 500, (40, 60))
    ])
    def test_si_rages(self, cod, ss, expected_range):
        """Test : plages attendues pour SI"""
        components = ASM1Fraction.fractionate(cod=cod, tss=ss)

        si = components['si']
        assert expected_range[0] <= si <= expected_range[1]

    def test_all_values_positive(self):
        """Test : toutes les valeurs sont positivies"""
        components = ASM1Fraction.fractionate(
            cod=500.0,
            tss=250.0,
            tkn=40.0,
            nh4=28.0
        )

        for key, value in components.items():
            assert value >= 0, f"{key} est négatif: {value}"


class TestASM2DFraction:
    """Tests pour ASM2DFraction"""

    def test_basic_fractionation(self):
        """Test : fractionnement basique ASM2d"""
        components = ASM2DFraction.fractionate(
            cod=500.0,
            tss=250.0,
            tkn=40.0,
            nh4=28.0,
            tp=10.0,
            po4=5.0
        )

        assert isinstance(components, dict)
        assert len(components) > 0

    def test_pao_components_present(self):
        """Test : composants PAO présents"""
        components = ASM2DFraction.fractionate(
            cod=500.0,
            tss=250.0,
            tkn=40.0,
            tp=10.0
        )

        for c in ['xpao', 'xpp', 'xpha', 'spo4']:
            assert c in components

    def test_phosphorus_balance(self):
        """Test : bilan du phosphore"""
        tp = 10.0

        components = ASM2DFraction.fractionate(
            cod=500.0,
            tss=250.0,
            tkn=40.0,
            tp=tp,
            po4=5.0
        )
        assert components['spo4'] == 5.0

        assert components['xpp'] > 0

    def test_fermentable_substrates(self):
        """Test : substrats fermentescibles"""
        components = ASM2DFraction.fractionate(
            cod=500.0,
            tss=250.0,
            rbcod=100.0
        )
        assert 'sf' in components
        assert 'sa' in components
        assert components['sf'] == 75.0
        assert components['sa'] == 25.0

    def test_tss_calculation(self):
        """Test : calcul des TSS"""
        comp1 = ASM2DFraction.fractionate(
            cod=500.0,
            tss=0.0,
            tkn=40.0
        )

        assert 'xtss' in comp1
        assert comp1['xtss'] > 0

        comp2 = ASM2DFraction.fractionate(
            cod=500.0,
            tss=250.0,
            tkn=40.0
        )

        assert 'xtss' in comp2
        assert comp2['xtss'] == 250.0

class TestASM3Fraction:
    """Tests pour ASM3Fraction"""

    def test_basic_fractionation(self):
        """Test : fractionnement basique ASM3"""
        components = ASM3Fraction.fractionate(
            cod=500.0,
            tss=250.0,
            tkn=40.0,
            nh4=28.0
        )

        assert isinstance(components, dict)

    def test_storage_component(self):
        """Test : composant de stockage"""
        components = ASM3Fraction.fractionate(
            cod=500.0,
            tss=250.0
        )
        assert 'xsto' in components
        assert components['xsto'] >= 0

@pytest.mark.parametrize('fraction_class', [
    ASM1Fraction,
    ASM2DFraction,
    ASM3Fraction
])
class TestAllFractions:
    """Tests génériques pour toutes les fractions"""

    def test_returns_dict(self, fraction_class):
        """Test : retourne un dictionnaire"""
        components = fraction_class.fractionate(
            cod=500.0,
            tss=250.0
        )
        assert isinstance(components, dict)

    def test_all_positivie(self, fraction_class):
        """Test : toutes les valeurs positives"""
        components = fraction_class.fractionate(
            cod=500.0,
            tss=250.0,
            tkn=40.0
        )

        for key, value in components.items():
            assert value >= 0, f"{fraction_class.__name__}: {key} négatif"

    def test_handles_zeros(self, fraction_class):
        """Test : gère les zéros"""
        components = fraction_class.fractionate(
            cod=500.0,
            tss=0.0,
            tkn=0.0
        )
        assert components is not None

    def test_very_low_cod(self, fraction_class):
        """Test : DCO très faible"""
        components = fraction_class.fractionate(
            cod=10.0,
            tss=5.0
        )

        assert components is not None
        assert all(v >= 0 for _, v in components.items())

    def test_very_high_cod(self, fraction_class):
        """Test : DCO très élevée"""
        components = fraction_class.fractionate(
            cod=5000.0,
            tss=2500.0
        )

        assert components is not None

    def test_cod_soluble_greater_than_total(self, fraction_class):
        """Test : DCO soluble > DCO totale (cas invalide)"""
        components = fraction_class.fractionate(
            cod=500.0,
            cod_soluble=600.0,
            tss=250.0
        )

        assert components is not None

    def test_no_optional_params(self, fraction_class):
        """Test : seulement le pramètre obligatoire"""
        components = fraction_class.fractionate(
            cod=500.0
        )
        assert components is not None
        assert 'si' in components

class TestFractionsLogging:
    """Tests des messages de logging"""

    @patch('models.empyrical.asm1.fraction.logger')
    def test_logs_debug_message_asm1(self, mock_logger):
        """Test : message de debug emis"""
        ASM1Fraction.fractionate(
            cod=500.0,
            tss=250.0
        )
        assert mock_logger.debug.called or mock_logger.info.called

    @patch('models.empyrical.asm2d.fraction.logger')
    def test_logs_debug_message_asm2d(self, mock_logger):
        """Test : message de debug emis"""
        ASM2DFraction.fractionate(
            cod=500.0,
            tss=250.0
        )
        assert mock_logger.debug.called or mock_logger.info.called

    @patch('models.empyrical.asm3.fraction.logger')
    def test_logs_debug_message_asm3(self, mock_logger):
        """Test : message de debug emis"""
        ASM3Fraction.fractionate(
            cod=500.0,
            tss=250.0
        )
        assert mock_logger.debug.called or mock_logger.info.called