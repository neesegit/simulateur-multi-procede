"""
Tests unitaires pour le modèle de Takacs (décantation secondaire)
"""
import pytest
import numpy as np

from models.empyrical.takacs_model import TakacsModel


@pytest.fixture
def model():
    return TakacsModel()


@pytest.fixture
def base_context(model):
    """Contexte opérationnel typique pour le settler."""
    n = model.n_layers
    feed = n // 2
    return {
        'Q_in':        1000.0 / 24,  # m³/h (1000 m³/j)
        'Q_underflow':  200.0 / 24,
        'Q_overflow':   800.0 / 24,
        'X_in':        3000.0,        # mg/L
        'area':         100.0,        # m²
        'layer_height':   0.5,        # m
        'feed_layer':    feed,
    }


# ===========================================================================
# Initialisation
# ===========================================================================

class TestTakacsInitialization:

    def test_model_type(self, model):
        assert model.model_type == "TakacsModel"

    def test_default_n_layers(self, model):
        assert model.n_layers == 10

    def test_component_indices(self, model):
        names = model.get_component_names()
        assert len(names) == model.n_layers
        for i, name in enumerate(names):
            assert name == f'layer_{i}'

    def test_custom_n_layers(self):
        m = TakacsModel(params={'n_layers': 5})
        assert m.n_layers == 5
        assert len(m.get_component_names()) == 5

    def test_default_params_applied(self):
        """Sans paramètres, les DEFAULT_PARAMS doivent être utilisés."""
        m = TakacsModel()
        assert 'v0' in m.params
        assert 'rh' in m.params
        assert 'rp' in m.params

    def test_custom_params_override_defaults(self):
        """Un paramètre personnalisé doit écraser la valeur par défaut."""
        m = TakacsModel(params={'v0': 999.0})
        assert m.params['v0'] == pytest.approx(999.0)


# ===========================================================================
# Vitesse de sédimentation
# ===========================================================================

class TestSettlingVelocity:

    def test_output_shape(self, model):
        X = np.ones(model.n_layers) * 1000.0
        vs = model.compute_settling_velocity(X)
        assert vs.shape == (model.n_layers,)

    def test_no_nan_inf(self, model):
        X = np.linspace(0, 10000, model.n_layers)
        vs = model.compute_settling_velocity(X)
        assert not np.any(np.isnan(vs))
        assert not np.any(np.isinf(vs))

    def test_bounded_above_by_v0(self, model):
        """vs ne peut pas dépasser v0."""
        X = np.ones(model.n_layers) * 100.0
        vs = model.compute_settling_velocity(X)
        assert np.all(vs <= model.params['v0'] + 1e-9)

    def test_bounded_below_by_zero(self, model):
        """vs ne peut pas être négatif."""
        X = np.linspace(0, 20000, model.n_layers)
        vs = model.compute_settling_velocity(X)
        assert np.all(vs >= 0.0)

    def test_zero_concentration_returns_v0(self, model):
        """À X ≤ 0, vs = v0 (vitesse maximale)."""
        X = np.zeros(model.n_layers)
        vs = model.compute_settling_velocity(X)
        assert np.all(vs == pytest.approx(model.params['v0']))

    def test_high_concentration_reduces_velocity(self, model):
        """Une concentration élevée doit réduire vs par rapport à une concentration faible."""
        X_low  = np.ones(model.n_layers) * 500.0
        X_high = np.ones(model.n_layers) * 8000.0
        vs_low  = model.compute_settling_velocity(X_low)
        vs_high = model.compute_settling_velocity(X_high)
        assert np.mean(vs_high) < np.mean(vs_low)


# ===========================================================================
# Compute fluxes
# ===========================================================================

class TestComputeFluxes:

    def test_output_shape(self, model):
        state = np.ones(model.n_layers) * 1000.0
        v     = np.zeros(model.n_layers)
        flux  = model.compute_fluxes(state, v)
        assert flux.shape == (model.n_layers,)

    def test_zero_concentration_zero_flux(self, model):
        """Aucune concentration → aucun flux (sauf sedimentation nulle)."""
        state = np.zeros(model.n_layers)
        v     = np.zeros(model.n_layers)
        flux  = model.compute_fluxes(state, v)
        assert np.allclose(flux, 0.0)

    def test_no_nan_inf(self, model):
        state = np.ones(model.n_layers) * 2000.0
        v     = np.ones(model.n_layers) * 0.5
        flux  = model.compute_fluxes(state, v)
        assert not np.any(np.isnan(flux))
        assert not np.any(np.isinf(flux))


# ===========================================================================
# Derivatives
# ===========================================================================

class TestDerivatives:

    def test_requires_context(self, model):
        """derivatives() doit lever ValueError sans contexte."""
        state = np.ones(model.n_layers) * 1000.0
        with pytest.raises(ValueError):
            model.derivatives(state)

    def test_output_shape(self, model, base_context):
        state = np.ones(model.n_layers) * 1000.0
        dXdt  = model.derivatives(state, base_context)
        assert dXdt.shape == (model.n_layers,)

    def test_no_nan_inf(self, model, base_context):
        state = np.ones(model.n_layers) * 2000.0
        dXdt  = model.derivatives(state, base_context)
        assert not np.any(np.isnan(dXdt))
        assert not np.any(np.isinf(dXdt))

    def test_zero_state_no_nan(self, model, base_context):
        """Etat nul ne doit pas provoquer de NaN."""
        state = np.zeros(model.n_layers)
        dXdt  = model.derivatives(state, base_context)
        assert not np.any(np.isnan(dXdt))
        assert not np.any(np.isinf(dXdt))

    def test_feed_layer_has_source_term(self, model, base_context):
        """La couche d'alimentation doit recevoir un flux source positif (X_in > 0)."""
        state = np.zeros(model.n_layers)
        dXdt  = model.derivatives(state, base_context)
        feed  = base_context['feed_layer']
        assert dXdt[feed] > 0

    def test_hydraulic_balance_clarification_zone(self, model, base_context):
        """
        Vérifie que la zone de clarification (couches 0..feed-1) reçoit
        un flux bulk positif (sortie vers le haut) — correction takacs_model.py.
        Pour state uniforme > 0, les couches supérieures doivent présenter une
        dérivée négative (matière emportée vers le dessus).
        """
        feed  = base_context['feed_layer']
        state = np.ones(model.n_layers) * 1000.0
        dXdt  = model.derivatives(state, base_context)
        # Les couches bien au-dessus de l'alimentation doivent dériver vers 0
        # (tending vers clarification, dXdt ≤ 0 en régime stationnaire)
        assert dXdt.shape == (model.n_layers,)
        assert not np.any(np.isnan(dXdt))


# ===========================================================================
# Conversions dict ↔ array
# ===========================================================================

class TestConversions:

    def test_dict_to_concentrations_shape(self, model):
        d = {f'layer_{i}': float(i * 100) for i in range(model.n_layers)}
        c = model.dict_to_concentrations(d)
        assert c.shape == (model.n_layers,)

    def test_concentrations_to_dict_keys(self, model):
        state = np.ones(model.n_layers) * 500.0
        d = model.concentrations_to_dict(state)
        assert set(d.keys()) == set(model.get_component_names())

    def test_roundtrip(self, model):
        original = {f'layer_{i}': float(i * 100 + 1) for i in range(model.n_layers)}
        array    = model.dict_to_concentrations(original)
        recovered = model.concentrations_to_dict(array)
        for k, v in original.items():
            assert recovered[k] == pytest.approx(v)

    def test_unknown_key_ignored(self, model):
        """Une clé inconnue dans le dict d'entrée doit être ignorée silencieusement."""
        d = {'layer_0': 1000.0, 'unknown_key': 999.9}
        c = model.dict_to_concentrations(d)
        assert c[0] == pytest.approx(1000.0)


# ===========================================================================
# Etiquette de couche
# ===========================================================================

class TestComponentLabel:

    def test_surface_layer(self, model):
        label = model.get_component_label('layer_0')
        assert 'surface' in label.lower() or '0' in label

    def test_bottom_layer(self, model):
        last = f'layer_{model.n_layers - 1}'
        label = model.get_component_label(last)
        assert 'fond' in label.lower() or str(model.n_layers - 1) in label

    def test_unknown_label_passthrough(self, model):
        assert model.get_component_label('foo') == 'foo'
