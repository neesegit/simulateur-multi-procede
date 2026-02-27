"""
Tests unitaires pour les calculateurs de métriques
(HRTCalculator, SRTCalculator, SVICalculator, EnergyConsumptionCalculator)
"""
import pytest

from core.registries.metrics.calculators.hrt import HRTCalculator
from core.registries.metrics.calculators.srt import SRTCalculator
from core.registries.metrics.calculators.svi import SVICalculator
from core.registries.metrics.calculators.energy import EnergyConsumptionCalculator


# ===========================================================================
# HRTCalculator
# ===========================================================================

class TestHRTCalculator:

    @pytest.fixture
    def calc(self):
        return HRTCalculator(min_hours=2.0, max_hours=48.0)

    def test_returns_hrt_hours_key(self, calc):
        result = calc.calculate({}, {'flowrate': 1000.0}, {'volume': 5000.0})
        assert 'hrt_hours' in result

    def test_normal_calculation(self, calc):
        """V=5000 m³, Q=1000 m³/h → HRT = 5 h."""
        result = calc.calculate({}, {'flowrate': 1000.0}, {'volume': 5000.0})
        assert result['hrt_hours'] == pytest.approx(5.0)

    def test_zero_flowrate_returns_zero(self, calc):
        """Q=0 → HRT = 0 (pas de clip, hrt_hours = 0 avant clip donne min)."""
        result = calc.calculate({}, {'flowrate': 0.0}, {'volume': 5000.0})
        # flowrate=0 → hrt=0 → clip → min_hours=2
        assert result['hrt_hours'] == pytest.approx(calc.min_hours)

    def test_clips_to_min(self, calc):
        """HRT calculé < min_hours → renvoyé = min_hours."""
        # V=100, Q=1000 → HRT=0.1h → clip à 2h
        result = calc.calculate({}, {'flowrate': 1000.0}, {'volume': 100.0})
        assert result['hrt_hours'] == pytest.approx(calc.min_hours)

    def test_clips_to_max(self, calc):
        """HRT calculé > max_hours → renvoyé = max_hours."""
        # V=100000, Q=1000 → HRT=100h → clip à 48h
        result = calc.calculate({}, {'flowrate': 1000.0}, {'volume': 100_000.0})
        assert result['hrt_hours'] == pytest.approx(calc.max_hours)

    def test_custom_bounds(self):
        calc = HRTCalculator(min_hours=1.0, max_hours=10.0)
        result = calc.calculate({}, {'flowrate': 1000.0}, {'volume': 100_000.0})
        assert result['hrt_hours'] == pytest.approx(10.0)

    def test_missing_keys_default_to_zero(self, calc):
        """flowrate et volume absents → HRT = 0 → clip à min."""
        result = calc.calculate({}, {}, {})
        assert result['hrt_hours'] == pytest.approx(calc.min_hours)


# ===========================================================================
# SRTCalculator
# ===========================================================================

class TestSRTCalculator:

    @pytest.fixture
    def calc(self):
        return SRTCalculator(min_days=3.0, max_days=50.0, fallback_days=20.0)

    def test_returns_srt_days_key(self, calc):
        result = calc.calculate(
            {'tss': 3000.0},
            {'flowrate': 1000.0},
            {'volume': 5000.0, 'waste_ratio': 0.01}
        )
        assert 'srt_days' in result

    def test_normal_calculation(self, calc):
        """
        mlss=3000, V=5000, Q=1000 m³/h, waste_ratio=0.01.
        waste_flow = 10 m³/h.
        total_solids = 3000*5000/1000 = 15000 kg.
        wasted/day = 10*3000*24/1000 = 720 kg/j.
        SRT = 15000/720 ≈ 20.83 j.
        """
        result = calc.calculate(
            {'tss': 3000.0},
            {'flowrate': 1000.0},
            {'volume': 5000.0, 'waste_ratio': 0.01}
        )
        assert result['srt_days'] == pytest.approx(20.83, rel=1e-2)

    def test_low_mlss_returns_fallback(self, calc):
        """MLSS < 100 → SRT = fallback."""
        result = calc.calculate(
            {'tss': 50.0},
            {'flowrate': 1000.0},
            {'volume': 5000.0, 'waste_ratio': 0.01}
        )
        assert result['srt_days'] == pytest.approx(calc.fallback_days)

    def test_zero_flowrate_returns_fallback(self, calc):
        """Q = 0 → SRT = fallback."""
        result = calc.calculate(
            {'tss': 3000.0},
            {'flowrate': 0.0},
            {'volume': 5000.0, 'waste_ratio': 0.01}
        )
        assert result['srt_days'] == pytest.approx(calc.fallback_days)

    def test_clips_to_min(self, calc):
        """SRT calculé très court → clip à min_days."""
        # waste_ratio=0.5, Q=1000, mlss=3000, V=5000 → très court
        result = calc.calculate(
            {'tss': 3000.0},
            {'flowrate': 1000.0},
            {'volume': 5000.0, 'waste_ratio': 0.5}
        )
        assert result['srt_days'] == pytest.approx(calc.min_days)

    def test_clips_to_max(self, calc):
        """SRT calculé très long → clip à max_days."""
        # waste_ratio=0.0001, Q=1000, mlss=3000, V=5000 → très long
        result = calc.calculate(
            {'tss': 3000.0},
            {'flowrate': 1000.0},
            {'volume': 5000.0, 'waste_ratio': 0.0001}
        )
        assert result['srt_days'] == pytest.approx(calc.max_days)

    def test_mlss_from_inputs_if_not_in_components(self, calc):
        """mlss lu dans inputs si absent de components → même résultat que via components."""
        result_from_inputs = calc.calculate(
            {},
            {'flowrate': 1000.0, 'tss': 3000.0},
            {'volume': 5000.0, 'waste_ratio': 0.01}
        )
        result_from_components = calc.calculate(
            {'tss': 3000.0},
            {'flowrate': 1000.0},
            {'volume': 5000.0, 'waste_ratio': 0.01}
        )
        assert result_from_inputs['srt_days'] == pytest.approx(result_from_components['srt_days'])


# ===========================================================================
# SVICalculator
# ===========================================================================

class TestSVICalculator:

    @pytest.fixture
    def calc(self):
        return SVICalculator(formula_numerator=300.0, min=50.0, max=300.0, fallback=120.0)

    def test_returns_svi_key(self, calc):
        result = calc.calculate({'tss': 3000.0}, {}, {})
        assert 'svi' in result

    def test_normal_calculation(self, calc):
        """mlss=3000 mg/L → 3 g/L → SVI = 300/3 = 100 mL/g."""
        result = calc.calculate({'tss': 3000.0}, {}, {})
        assert result['svi'] == pytest.approx(100.0)

    def test_low_mlss_returns_fallback(self, calc):
        """MLSS < 100 → SVI = fallback."""
        result = calc.calculate({'tss': 50.0}, {}, {})
        assert result['svi'] == pytest.approx(calc.fallback)

    def test_clips_to_min(self, calc):
        """SVI calculé < 50 → renvoyé = 50."""
        # mlss=10000 → SVI=30 → clip à 50
        result = calc.calculate({'tss': 10_000.0}, {}, {})
        assert result['svi'] == pytest.approx(calc.min)

    def test_clips_to_max(self, calc):
        """SVI calculé > 300 → renvoyé = 300."""
        # mlss=150 → SVI=2000 → clip à 300
        result = calc.calculate({'tss': 150.0}, {}, {})
        assert result['svi'] == pytest.approx(calc.max)

    def test_mlss_from_inputs_if_not_in_components(self, calc):
        """mlss lu dans inputs si absent de components."""
        result = calc.calculate({}, {'tss': 3000.0}, {})
        assert result['svi'] == pytest.approx(100.0)

    def test_zero_mlss_returns_fallback(self, calc):
        result = calc.calculate({'tss': 0.0}, {}, {})
        assert result['svi'] == pytest.approx(calc.fallback)


# ===========================================================================
# EnergyConsumptionCalculator
# ===========================================================================

class TestEnergyConsumptionCalculator:

    @pytest.fixture
    def calc(self):
        return EnergyConsumptionCalculator()

    def _inputs(self, cod_in=300.0, cod_out=30.0, flowrate=1000.0, dt=1.0):
        return {
            'cod_soluble_in':  cod_in,
            'cod_soluble_out': cod_out,
            'flowrate':        flowrate,
        }

    def test_returns_expected_keys(self, calc):
        result = calc.calculate({}, self._inputs(), {'dt': 1.0})
        assert 'oxygen_consumed_kg' in result
        assert 'aeration_energy_kwh' in result
        assert 'energy_per_m3' in result

    def test_normal_calculation(self, calc):
        """
        cod_removed = 270 mg/L, Q=1000 m³/h, dt=1h.
        O2 = 270*1000*1/1000 = 270 kg.
        energy = 270*2 = 540 kWh.
        energy/m3 = 540/1000 = 0.54 kWh/m3.
        """
        result = calc.calculate({}, self._inputs(), {'dt': 1.0})
        assert result['oxygen_consumed_kg']  == pytest.approx(270.0)
        assert result['aeration_energy_kwh'] == pytest.approx(540.0)
        assert result['energy_per_m3']       == pytest.approx(0.54)

    def test_no_removal_gives_zero_energy(self, calc):
        """cod_in == cod_out → 0 kg O2 → 0 kWh."""
        result = calc.calculate(
            {}, self._inputs(cod_in=300.0, cod_out=300.0), {'dt': 1.0}
        )
        assert result['oxygen_consumed_kg']  == pytest.approx(0.0)
        assert result['aeration_energy_kwh'] == pytest.approx(0.0)

    def test_cod_out_exceeds_cod_in_clamped_to_zero(self, calc):
        """cod_out > cod_in ne doit pas donner d'énergie négative."""
        result = calc.calculate(
            {}, self._inputs(cod_in=100.0, cod_out=300.0), {'dt': 1.0}
        )
        assert result['oxygen_consumed_kg']  >= 0.0
        assert result['aeration_energy_kwh'] >= 0.0

    def test_zero_flowrate_gives_zero_energy(self, calc):
        result = calc.calculate(
            {}, self._inputs(flowrate=0.0), {'dt': 1.0}
        )
        assert result['aeration_energy_kwh'] == pytest.approx(0.0)
        assert result['energy_per_m3']       == pytest.approx(0.0)

    def test_fallback_to_cod_in_without_soluble_key(self, calc):
        """Fallback sur cod_in / cod_out si cod_soluble_in est absent."""
        inputs = {'cod_in': 300.0, 'cod_out': 30.0, 'flowrate': 1000.0}
        result = calc.calculate({}, inputs, {'dt': 1.0})
        assert result['oxygen_consumed_kg'] == pytest.approx(270.0)

    def test_energy_per_m3_formula(self, calc):
        """energy_per_m3 = aeration_energy / total_volume."""
        result = calc.calculate({}, self._inputs(flowrate=500.0), {'dt': 2.0})
        total_volume = 500.0 * 2.0
        expected = result['aeration_energy_kwh'] / total_volume
        assert result['energy_per_m3'] == pytest.approx(expected)
