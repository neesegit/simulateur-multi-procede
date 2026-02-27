"""
Tests d'intégration — pipeline métriques

Vérifie la chaîne :
  Fractionnement → composants → MetricsRegistry.calculate_all_for_model() → métriques
"""
import pytest

from models.empyrical.asm1.fraction import ASM1Fraction
from models.empyrical.asm2d.fraction import ASM2DFraction
from models.empyrical.asm3.fraction import ASM3Fraction

from core.registries.metrics.registry import MetricsRegistry


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _registry() -> MetricsRegistry:
    # Réinitialiser le singleton pour éviter la contamination entre tests
    MetricsRegistry._instance = None
    return MetricsRegistry.get_instance()


def _base_inputs(flowrate: float = 1000.0) -> dict:
    return {
        'flowrate':        flowrate,
        'cod_soluble_in':  200.0,
        'cod_soluble_out':  20.0,
        'tss':            3000.0,
    }


def _base_context(volume: float = 5000.0) -> dict:
    return {
        'volume':      volume,
        'dt':          1.0,        # 1 heure
        'waste_ratio': 0.01,
    }


# ===========================================================================
# MetricsRegistry — enregistrement par défaut
# ===========================================================================

class TestMetricsRegistryDefaults:

    def test_hrt_registered(self):
        reg = _registry()
        assert reg.is_registered('hrt')

    def test_srt_registered(self):
        reg = _registry()
        assert reg.is_registered('srt')

    def test_svi_registered(self):
        reg = _registry()
        assert reg.is_registered('svi')

    def test_energy_registered(self):
        reg = _registry()
        assert reg.is_registered('energy')

    def test_cod_not_registered(self):
        """'cod' n'a pas de calculateur — model_metrics.json corrigé."""
        reg = _registry()
        assert not reg.is_registered('cod')

    def test_asm1_model_metrics_list(self):
        reg = _registry()
        metrics = reg.get_model_metrics('ASM1Model')
        assert 'hrt'    in metrics
        assert 'srt'    in metrics
        assert 'svi'    in metrics
        assert 'energy' in metrics
        assert 'cod'    not in metrics

    def test_asm2d_model_metrics_list(self):
        reg = _registry()
        metrics = reg.get_model_metrics('ASM2dModel')
        assert 'hrt' in metrics
        assert 'srt' in metrics

    def test_asm3_model_metrics_list(self):
        reg = _registry()
        metrics = reg.get_model_metrics('ASM3Model')
        assert set(reg.get_model_metrics('ASM3Model')) == set(reg.get_model_metrics('ASM1Model'))


# ===========================================================================
# calculate() individuel
# ===========================================================================

class TestIndividualCalculate:

    def test_hrt_calculate(self):
        reg = _registry()
        result = reg.calculate('hrt', {}, _base_inputs(), _base_context())
        assert 'hrt_hours' in result
        assert result['hrt_hours'] == pytest.approx(5.0)  # 5000/1000

    def test_srt_calculate(self):
        reg = _registry()
        result = reg.calculate('srt', {'tss': 3000.0}, _base_inputs(), _base_context())
        assert 'srt_days' in result
        assert result['srt_days'] > 0

    def test_svi_calculate(self):
        reg = _registry()
        result = reg.calculate('svi', {'tss': 3000.0}, _base_inputs(), _base_context())
        assert 'svi' in result
        assert result['svi'] == pytest.approx(100.0)  # 300 / 3

    def test_energy_calculate(self):
        reg = _registry()
        result = reg.calculate('energy', {}, _base_inputs(), _base_context())
        assert 'aeration_energy_kwh' in result
        assert result['aeration_energy_kwh'] > 0

    def test_unknown_metric_raises(self):
        reg = _registry()
        with pytest.raises(ValueError, match="not registered"):
            reg.calculate('unknown_metric', {}, {}, {})


# ===========================================================================
# calculate_all_for_model()
# ===========================================================================

class TestCalculateAllForModel:

    @pytest.fixture
    def reg(self):
        return _registry()

    def test_asm1_all_metrics_computed(self, reg):
        result = reg.calculate_all_for_model(
            'ASM1Model',
            components={'tss': 3000.0},
            inputs=_base_inputs(),
            context=_base_context()
        )
        assert 'hrt_hours'           in result
        assert 'srt_days'            in result
        assert 'svi'                 in result
        assert 'aeration_energy_kwh' in result

    def test_asm1_no_error_without_tss(self, reg):
        """Sans TSS, les calculateurs doivent utiliser leurs fallbacks."""
        result = reg.calculate_all_for_model(
            'ASM1Model',
            components={},
            inputs=_base_inputs(),
            context=_base_context()
        )
        # SRT et SVI retournent leurs fallbacks, pas d'exception
        assert 'srt_days' in result
        assert 'svi'      in result

    def test_asm2d_all_metrics_computed(self, reg):
        result = reg.calculate_all_for_model(
            'ASM2dModel',
            components={'tss': 2500.0},
            inputs=_base_inputs(),
            context=_base_context()
        )
        assert 'hrt_hours'           in result
        assert 'aeration_energy_kwh' in result

    def test_unknown_model_returns_empty(self, reg):
        """Un modèle inconnu → aucune métrique → dict vide."""
        result = reg.calculate_all_for_model(
            'UnknownModel',
            components={},
            inputs={},
            context={}
        )
        assert result == {}


# ===========================================================================
# Pipeline fractionation → métriques
# ===========================================================================

class TestFractionationToMetricsPipeline:
    """
    Vérifie que les composants issus du fractionnement peuvent être passés
    directement au registre de métriques sans transformation supplémentaire.
    """

    def test_asm1_fractionation_then_hrt(self):
        components = ASM1Fraction.fractionate(
            cod=500.0, tss=250.0, tkn=40.0, nh4=28.0
        )
        reg = _registry()
        result = reg.calculate(
            'hrt', components,
            inputs={'flowrate': 1000.0},
            context={'volume': 5000.0, 'dt': 1.0}
        )
        assert 'hrt_hours' in result
        assert result['hrt_hours'] > 0

    def test_asm2d_fractionation_then_svi(self):
        components = ASM2DFraction.fractionate(
            cod=500.0, tss=250.0, tkn=40.0, nh4=28.0, po4=8.0
        )
        # Fournir tss via inputs (les composants ASM2d ne contiennent pas 'tss' directement)
        reg = _registry()
        result = reg.calculate(
            'svi', components,
            inputs={'tss': 3000.0},
            context={}
        )
        assert 'svi' in result

    def test_asm3_fractionation_then_energy(self):
        components = ASM3Fraction.fractionate(
            cod=500.0, tss=250.0, tkn=40.0, nh4=28.0
        )
        reg = _registry()
        result = reg.calculate(
            'energy', components,
            inputs={'flowrate': 1000.0, 'cod_soluble_in': 200.0, 'cod_soluble_out': 20.0},
            context={'dt': 1.0}
        )
        assert 'aeration_energy_kwh' in result
        assert result['aeration_energy_kwh'] >= 0


# ===========================================================================
# Cohérence des valeurs calculées
# ===========================================================================

class TestMetricsValueCoherence:

    def test_hrt_increases_with_volume(self):
        reg = _registry()
        r1 = reg.calculate('hrt', {}, _base_inputs(), _base_context(volume=1000.0))
        r2 = reg.calculate('hrt', {}, _base_inputs(), _base_context(volume=5000.0))
        assert r2['hrt_hours'] > r1['hrt_hours']

    def test_svi_decreases_with_higher_mlss(self):
        reg = _registry()
        r1 = reg.calculate('svi', {'tss': 2000.0}, _base_inputs(), _base_context())
        r2 = reg.calculate('svi', {'tss': 4000.0}, _base_inputs(), _base_context())
        assert r2['svi'] < r1['svi']

    def test_energy_increases_with_cod_removal(self):
        reg = _registry()
        inputs_low  = {**_base_inputs(), 'cod_soluble_in': 100.0, 'cod_soluble_out': 90.0}
        inputs_high = {**_base_inputs(), 'cod_soluble_in': 500.0, 'cod_soluble_out': 10.0}
        r1 = reg.calculate('energy', {}, inputs_low,  _base_context())
        r2 = reg.calculate('energy', {}, inputs_high, _base_context())
        assert r2['aeration_energy_kwh'] > r1['aeration_energy_kwh']
