"""
Tests unitaires pour les fonctions de cinétique et stœchiométrie ASM1 / ASM2d / ASM3
"""
import pytest
import numpy as np

from models.empyrical.asm1.kinetics import calculate_process_rates as asm1_kinetics
from models.empyrical.asm1.stoichiometry import build_stoichiometric_matrix as asm1_stoich

from models.empyrical.asm2d.kinetics import calculate_process_rates as asm2d_kinetics
from models.empyrical.asm2d.stoichiometry import build_stoichiometric_matrix as asm2d_stoich

from models.empyrical.asm3.kinetics import calculate_process_rates as asm3_kinetics
from models.empyrical.asm3.stoichiometry import build_stoichiometric_matrix as asm3_stoich

from models.empyrical.asm1.model import ASM1Model
from models.empyrical.asm2d.model import ASM2dModel
from models.empyrical.asm3.model import ASM3Model


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _asm1_conc(ss=100.0, xs=200.0, xbh=2000.0, xba=100.0,
               so=2.0, sno=5.0, snh=20.0, snd=2.0, xnd=5.0,
               si=30.0, xi=50.0, xp=400.0, salk=7.0):
    """Vecteur de concentrations ASM1 (13 composants dans l'ordre du modèle)."""
    model = ASM1Model()
    idx = model.COMPONENT_INDICES
    c = np.zeros(13)
    c[idx['si']]   = si
    c[idx['ss']]   = ss
    c[idx['xi']]   = xi
    c[idx['xs']]   = xs
    c[idx['xbh']]  = xbh
    c[idx['xba']]  = xba
    c[idx['xp']]   = xp
    c[idx['so']]   = so
    c[idx['sno']]  = sno
    c[idx['snh']]  = snh
    c[idx['snd']]  = snd
    c[idx['xnd']]  = xnd
    c[idx['salk']] = salk
    return c


def _asm2d_conc_positive():
    """Vecteur de concentrations ASM2d (19 composants) positif typique."""
    c = np.zeros(19)
    c[0]  = 2.0    # SO2
    c[1]  = 100.0  # SF
    c[2]  = 50.0   # SA
    c[3]  = 20.0   # SNH4
    c[4]  = 5.0    # SNO3
    c[5]  = 5.0    # SPO4
    c[6]  = 30.0   # SI
    c[7]  = 7.0    # SALK
    c[8]  = 1.0    # SN2
    c[9]  = 50.0   # XI
    c[10] = 200.0  # XS
    c[11] = 2000.0 # XH
    c[12] = 100.0  # XPAO
    c[13] = 50.0   # XPP
    c[14] = 50.0   # XPHA
    c[15] = 80.0   # XAUT
    c[16] = 3000.0 # XTSS
    c[17] = 20.0   # XMEOH
    c[18] = 10.0   # XMEP
    return c


def _asm3_conc_positive():
    """Vecteur de concentrations ASM3 (13 composants) positif typique."""
    c = np.zeros(13)
    c[0]  = 2.0    # SO2
    c[1]  = 30.0   # SI
    c[2]  = 100.0  # SS
    c[3]  = 20.0   # SNH4
    c[4]  = 1.0    # SN2
    c[5]  = 5.0    # SNOX
    c[6]  = 7.0    # SALK
    c[7]  = 50.0   # XI
    c[8]  = 200.0  # XS
    c[9]  = 2000.0 # XH
    c[10] = 100.0  # XSTO
    c[11] = 80.0   # XA
    c[12] = 2500.0 # XSS
    return c


# ===========================================================================
# ASM1 — cinétique
# ===========================================================================

class TestASM1Kinetics:

    @pytest.fixture
    def params(self):
        return ASM1Model().params

    def test_shape(self, params):
        """Le vecteur rho doit avoir 8 éléments (8 processus ASM1)."""
        rho = asm1_kinetics(_asm1_conc(), params)
        assert rho.shape == (8,)

    def test_no_nan_inf_at_positive_concentrations(self, params):
        """Aucun NaN/inf pour des concentrations positives typiques."""
        rho = asm1_kinetics(_asm1_conc(), params)
        assert not np.any(np.isnan(rho))
        assert not np.any(np.isinf(rho))

    def test_no_nan_inf_at_zero_concentrations(self, params):
        """Aucun NaN/inf pour des concentrations nulles."""
        rho = asm1_kinetics(np.zeros(13), params)
        assert not np.any(np.isnan(rho))
        assert not np.any(np.isinf(rho))

    def test_aerobic_growth_positive_in_aerobic_conditions(self, params):
        """rho[0] (croissance aérobie) > 0 si SS > 0 et SO > 0."""
        c = _asm1_conc(ss=100.0, so=2.0, xbh=2000.0)
        rho = asm1_kinetics(c, params)
        assert rho[0] > 0

    def test_aerobic_growth_zero_without_substrate(self, params):
        """rho[0] = 0 si SS = 0."""
        c = _asm1_conc(ss=0.0, so=2.0, xbh=2000.0)
        rho = asm1_kinetics(c, params)
        assert rho[0] == 0.0

    def test_aerobic_growth_zero_without_oxygen(self, params):
        """rho[0] = 0 si SO = 0."""
        c = _asm1_conc(ss=100.0, so=0.0, xbh=2000.0)
        rho = asm1_kinetics(c, params)
        assert rho[0] == 0.0

    def test_anoxic_growth_inhibited_by_oxygen(self, params):
        """rho[1] (dénitrification) < rho[1] en anoxie stricte quand SO augmente."""
        c_anox = _asm1_conc(ss=100.0, so=0.01, sno=5.0, xbh=2000.0)
        c_aero = _asm1_conc(ss=100.0, so=4.0,  sno=5.0, xbh=2000.0)
        rho_anox = asm1_kinetics(c_anox, params)
        rho_aero = asm1_kinetics(c_aero, params)
        assert rho_anox[1] > rho_aero[1]

    def test_nitrification_positive_with_nh4_and_oxygen(self, params):
        """rho[2] (nitrification) > 0 si SNH > 0 et SO > 0."""
        c = _asm1_conc(snh=20.0, so=2.0, xba=100.0)
        rho = asm1_kinetics(c, params)
        assert rho[2] > 0

    def test_decay_rates_non_negative(self, params):
        """Les vitesses de décès (rho[3] et rho[4]) doivent être ≥ 0."""
        c = _asm1_conc(xbh=2000.0, xba=100.0)
        rho = asm1_kinetics(c, params)
        assert rho[3] >= 0
        assert rho[4] >= 0

    def test_all_rates_non_negative(self, params):
        """Toutes les vitesses de processus doivent être ≥ 0."""
        rho = asm1_kinetics(_asm1_conc(), params)
        assert np.all(rho >= 0)

    @pytest.mark.parametrize('scale', [1, 10, 100, 1000])
    def test_numerical_stability_at_various_concentrations(self, params, scale):
        """Stabilité numérique pour différents ordres de grandeur."""
        c = np.ones(13) * scale
        rho = asm1_kinetics(c, params)
        assert not np.any(np.isnan(rho))
        assert not np.any(np.isinf(rho))


# ===========================================================================
# ASM1 — stœchiométrie
# ===========================================================================

class TestASM1Stoichiometry:

    @pytest.fixture
    def S(self):
        return asm1_stoich(ASM1Model().params)

    def test_shape(self, S):
        """La matrice doit être de dimension (8, 13)."""
        assert S.shape == (8, 13)

    def test_aerobic_growth_consumes_ss(self, S):
        """Processus 1 : SS consommé (S[0,1] < 0)."""
        assert S[0, 1] < 0

    def test_aerobic_growth_produces_xbh(self, S):
        """Processus 1 : XBH produit (S[0,4] == 1)."""
        assert S[0, 4] == pytest.approx(1.0)

    def test_aerobic_growth_consumes_oxygen(self, S):
        """Processus 1 : O2 consommé (S[0,7] < 0)."""
        assert S[0, 7] < 0

    def test_anoxic_growth_consumes_no3(self, S):
        """Processus 2 : SNO consommé (S[1,8] < 0)."""
        assert S[1, 8] < 0

    def test_nitrification_produces_no3(self, S):
        """Processus 3 : SNO produit par nitrification (S[2,8] > 0)."""
        assert S[2, 8] > 0

    def test_nitrification_consumes_nh4(self, S):
        """Processus 3 : SNH consommé par nitrification (S[2,9] < 0)."""
        assert S[2, 9] < 0

    def test_decay_consumes_biomass(self, S):
        """Processus 4 : XBH consommé lors du décès (S[3,4] == -1)."""
        assert S[3, 4] == pytest.approx(-1.0)

    def test_hydrolysis_produces_ss(self, S):
        """Processus 7 : SS produit par hydrolyse (S[6,1] == 1)."""
        assert S[6, 1] == pytest.approx(1.0)

    def test_hydrolysis_consumes_xs(self, S):
        """Processus 7 : XS consommé par hydrolyse (S[6,3] == -1)."""
        assert S[6, 3] == pytest.approx(-1.0)


# ===========================================================================
# ASM2d — cinétique
# ===========================================================================

class TestASM2dKinetics:

    @pytest.fixture
    def params(self):
        return ASM2dModel().params

    def test_shape(self, params):
        """Le vecteur rho doit avoir 21 éléments (21 processus ASM2d)."""
        rho = asm2d_kinetics(_asm2d_conc_positive(), params)
        assert rho.shape == (21,)

    def test_no_nan_inf_at_positive_concentrations(self, params):
        """Aucun NaN/inf pour des concentrations positives typiques."""
        rho = asm2d_kinetics(_asm2d_conc_positive(), params)
        assert not np.any(np.isnan(rho))
        assert not np.any(np.isinf(rho))

    def test_no_nan_inf_at_zero_concentrations(self, params):
        """Aucun NaN/inf avec des concentrations nulles (protection 1e-10)."""
        rho = asm2d_kinetics(np.zeros(19), params)
        assert not np.any(np.isnan(rho))
        assert not np.any(np.isinf(rho))

    def test_all_rates_non_negative(self, params):
        """Toutes les vitesses de processus doivent être ≥ 0."""
        rho = asm2d_kinetics(_asm2d_conc_positive(), params)
        assert np.all(rho >= 0)

    @pytest.mark.parametrize('scale', [1, 10, 100])
    def test_numerical_stability(self, params, scale):
        c = np.ones(19) * scale
        rho = asm2d_kinetics(c, params)
        assert not np.any(np.isnan(rho))
        assert not np.any(np.isinf(rho))

    def test_aerobic_xaut_growth_positive(self, params):
        """rho[17] (croissance aérobie XAUT) > 0 en conditions aérobies."""
        c = _asm2d_conc_positive()
        c[0] = 4.0   # SO2 élevé
        c[3] = 20.0  # SNH4 disponible
        c[15] = 100.0 # XAUT présent
        rho = asm2d_kinetics(c, params)
        assert rho[17] > 0

    def test_alkalinity_monod_term_not_constant(self, params):
        """rho[17] varie avec SALK — vérifie que le terme Monod k_alk_aut+salk est correct."""
        c_high_alk = _asm2d_conc_positive()
        c_low_alk  = _asm2d_conc_positive()
        c_high_alk[7] = 10.0
        c_low_alk[7]  = 0.01
        rho_high = asm2d_kinetics(c_high_alk, params)
        rho_low  = asm2d_kinetics(c_low_alk, params)
        # Si le terme était k_alk_aut*salk, rho[17] serait constant. Avec +, il doit varier.
        assert rho_high[17] != pytest.approx(rho_low[17], rel=1e-3)


# ===========================================================================
# ASM2d — stœchiométrie
# ===========================================================================

class TestASM2dStoichiometry:

    @pytest.fixture
    def S(self):
        return asm2d_stoich(ASM2dModel().params)

    def test_shape(self, S):
        """La matrice doit être de dimension (21, 19)."""
        assert S.shape == (21, 19)

    def test_reaction7_sno3_consumed(self, S):
        """Réaction 7 (index 6) : SNO3 (index 4) consommé → S[6,4] < 0."""
        assert S[6, 4] < 0

    def test_reaction7_sn2_produced(self, S):
        """Réaction 7 (index 6) : SN2 (index 8) produit → S[6,8] > 0 (correction du signe)."""
        assert S[6, 8] > 0

    def test_reaction6_sno3_consumed(self, S):
        """Réaction 6 (index 5) : SNO3 (index 4) consommé → S[5,4] < 0."""
        assert S[5, 4] < 0

    def test_aerobic_growth_xh_produces_biomass(self, S):
        """Réaction 4 (index 3) : XH (index 11) produit → S[3,11] > 0."""
        assert S[3, 11] > 0

    def test_aerobic_growth_xh_consumes_sf(self, S):
        """Réaction 4 (index 3) : SF (index 1) consommé → S[3,1] < 0."""
        assert S[3, 1] < 0


# ===========================================================================
# ASM3 — cinétique
# ===========================================================================

class TestASM3Kinetics:

    @pytest.fixture
    def params(self):
        return ASM3Model().params

    def test_shape(self, params):
        """Le vecteur rho doit avoir 12 éléments (12 processus ASM3)."""
        rho = asm3_kinetics(_asm3_conc_positive(), params)
        assert rho.shape == (12,)

    def test_no_nan_inf_at_positive_concentrations(self, params):
        """Aucun NaN/inf pour des concentrations positives."""
        rho = asm3_kinetics(_asm3_conc_positive(), params)
        assert not np.any(np.isnan(rho))
        assert not np.any(np.isinf(rho))

    def test_no_nan_inf_at_zero_concentrations(self, params):
        """Aucun NaN/inf avec des concentrations nulles (protection 1e-6)."""
        rho = asm3_kinetics(np.zeros(13), params)
        assert not np.any(np.isnan(rho))
        assert not np.any(np.isinf(rho))

    def test_all_rates_non_negative(self, params):
        """Toutes les vitesses doivent être ≥ 0."""
        rho = asm3_kinetics(_asm3_conc_positive(), params)
        assert np.all(rho >= 0)

    @pytest.mark.parametrize('scale', [1, 10, 100])
    def test_numerical_stability(self, params, scale):
        c = np.ones(13) * scale
        rho = asm3_kinetics(c, params)
        assert not np.any(np.isnan(rho))
        assert not np.any(np.isinf(rho))


# ===========================================================================
# ASM3 — stœchiométrie
# ===========================================================================

class TestASM3Stoichiometry:

    @pytest.fixture
    def S(self):
        return asm3_stoich(ASM3Model().params)

    def test_shape(self, S):
        """La matrice doit être de dimension (12, 13)."""
        assert S.shape == (12, 13)

    def test_no_nan_inf(self, S):
        """Aucun NaN/inf dans la matrice stœchiométrique."""
        assert not np.any(np.isnan(S))
        assert not np.any(np.isinf(S))
