"""
Tests unitaires pour InfluentInitializer
"""
import pytest
from datetime import datetime

from core.orchestrator.influent_initializer import InfluentInitializer
from core.data.flow_data import FlowData


TIMESTAMP = datetime(2025, 1, 1, 0, 0, 0)

FULL_CONFIG = {
    'influent': {
        'flowrate': 1200.0,
        'temperature': 18.5,
        'composition': {
            'cod':        500.0,
            'tss':        250.0,
            'tkn':        40.0,
            'bod':        220.0,
            'nh4':        28.0,
            'no3':        0.5,
            'po4':        8.0,
            'alkalinity': 6.0,
        }
    }
}


class TestInfluentInitializerBasic:

    def test_returns_flow_data(self):
        flow = InfluentInitializer.create_from_config(FULL_CONFIG, TIMESTAMP)
        assert isinstance(flow, FlowData)

    def test_source_node_is_influent(self):
        flow = InfluentInitializer.create_from_config(FULL_CONFIG, TIMESTAMP)
        assert flow.source_node == 'influent'

    def test_timestamp_set(self):
        flow = InfluentInitializer.create_from_config(FULL_CONFIG, TIMESTAMP)
        assert flow.timestamp == TIMESTAMP

    def test_flowrate_from_config(self):
        flow = InfluentInitializer.create_from_config(FULL_CONFIG, TIMESTAMP)
        assert flow.flowrate == pytest.approx(1200.0)

    def test_temperature_from_config(self):
        flow = InfluentInitializer.create_from_config(FULL_CONFIG, TIMESTAMP)
        assert flow.temperature == pytest.approx(18.5)

    def test_composition_fields(self):
        flow = InfluentInitializer.create_from_config(FULL_CONFIG, TIMESTAMP)
        assert flow.cod        == pytest.approx(500.0)
        assert flow.tss        == pytest.approx(250.0)
        assert flow.tkn        == pytest.approx(40.0)
        assert flow.bod        == pytest.approx(220.0)
        assert flow.nh4        == pytest.approx(28.0)
        assert flow.no3        == pytest.approx(0.5)
        assert flow.po4        == pytest.approx(8.0)
        assert flow.alkalinity == pytest.approx(6.0)


class TestInfluentInitializerDefaults:

    def test_default_flowrate_when_missing(self):
        """Sans flowrate dans la config, la valeur par défaut est 1000."""
        config = {'influent': {'composition': {'cod': 500.0}}}
        flow = InfluentInitializer.create_from_config(config, TIMESTAMP)
        assert flow.flowrate == pytest.approx(1000.0)

    def test_default_temperature_when_missing(self):
        """Sans temperature dans la config, la valeur par défaut est 20.0."""
        config = {'influent': {'flowrate': 500.0, 'composition': {}}}
        flow = InfluentInitializer.create_from_config(config, TIMESTAMP)
        assert flow.temperature == pytest.approx(20.0)

    def test_composition_field_defaults_to_zero(self):
        """Un champ absent de la composition vaut 0."""
        config = {'influent': {'flowrate': 1000.0, 'composition': {'cod': 500.0}}}
        flow = InfluentInitializer.create_from_config(config, TIMESTAMP)
        assert flow.nh4 == pytest.approx(0.0)
        assert flow.no3 == pytest.approx(0.0)
        assert flow.po4 == pytest.approx(0.0)

    def test_empty_config_uses_defaults(self):
        """Config entièrement vide → valeurs par défaut."""
        flow = InfluentInitializer.create_from_config({}, TIMESTAMP)
        assert flow.flowrate    == pytest.approx(1000.0)
        assert flow.temperature == pytest.approx(20.0)

    def test_no_influent_key_uses_defaults(self):
        """Config sans clé 'influent' → valeurs par défaut."""
        flow = InfluentInitializer.create_from_config({'name': 'test'}, TIMESTAMP)
        assert flow.flowrate == pytest.approx(1000.0)


class TestInfluentInitializerSSAlias:

    def test_ss_alias_sets_tss(self):
        """La clé 'ss' dans la composition est un alias pour 'tss'."""
        config = {
            'influent': {
                'flowrate': 1000.0,
                'composition': {'ss': 300.0}
            }
        }
        flow = InfluentInitializer.create_from_config(config, TIMESTAMP)
        assert flow.tss == pytest.approx(300.0)

    def test_tss_takes_precedence_over_ss(self):
        """Si 'tss' est présent, il prime sur 'ss'."""
        config = {
            'influent': {
                'flowrate': 1000.0,
                'composition': {'tss': 250.0, 'ss': 999.0}
            }
        }
        flow = InfluentInitializer.create_from_config(config, TIMESTAMP)
        assert flow.tss == pytest.approx(250.0)

    def test_ss_absent_tss_absent_gives_zero(self):
        config = {'influent': {'flowrate': 1000.0, 'composition': {}}}
        flow = InfluentInitializer.create_from_config(config, TIMESTAMP)
        assert flow.tss == pytest.approx(0.0)
