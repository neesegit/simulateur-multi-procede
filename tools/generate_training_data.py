"""
Générateur de données d'entraînement pour les modèles ML (LinearModel, RandomForestModel).

Principe : simule N scénarios avec ASM1 jusqu'à l'état quasi-stationnaire,
puis enregistre les paires (influent + paramètres réacteur) → (effluent) dans un CSV.

Ce script est ISOLÉ du reste de la simulation — il ne sera plus nécessaire
quand des données réelles seront disponibles.

Usage :
    python tools/generate_training_data.py
    python tools/generate_training_data.py --n 2000 --output data/processed/custom.csv
    python tools/generate_training_data.py --seed 123
"""
import sys
import argparse
import logging
from pathlib import Path

# Ajoute la racine du projet au path pour pouvoir importer les modules internes
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import numpy as np
import pandas as pd

from models.empyrical.asm1.model import ASM1Model
from models.empyrical.asm1.fraction import ASM1Fraction
from core.solver.cstr_solver import CSTRSolver

logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Plages de variation des scénarios influent + réacteur
# ---------------------------------------------------------------------------
INFLUENT_RANGES = {
    'flowrate':    (500.0,  2500.0),   # m³/h
    'cod':         (200.0,  800.0),    # mg/L DCO totale
    'tss':         (100.0,  400.0),    # mg/L MES
    'tkn':         (20.0,   70.0),     # mg/L NTK
    'nh4':         (10.0,   55.0),     # mg/L NH4
    'no3':         (0.0,    5.0),      # mg/L NO3
    'temperature': (10.0,   25.0),     # °C
}
REACTOR_RANGES = {
    'volume':      (1000.0, 15000.0),  # m³
    'do_setpoint': (1.5,    4.0),      # mg/L O2
    'waste_ratio': (0.005,  0.03),     # fraction purge journalière
}

# Simulation jusqu'au pseudo-état-stationnaire
STEADY_STATE_DAYS = 60      # durée totale simulée
DT_DAYS           = 0.1     # pas de temps (jours)
N_STEPS           = int(STEADY_STATE_DAYS / DT_DAYS)


def _sample_scenarios(n: int, rng: np.random.Generator) -> list[dict]:
    """Génère n scénarios par échantillonnage aléatoire uniforme."""
    scenarios = []
    all_ranges = {**INFLUENT_RANGES, **REACTOR_RANGES}
    for _ in range(n):
        s = {}
        for key, (lo, hi) in all_ranges.items():
            s[key] = float(rng.uniform(lo, hi))
        # nh4 ne peut pas dépasser tkn
        s['nh4'] = min(s['nh4'], s['tkn'] * 0.85)
        scenarios.append(s)
    return scenarios


def _run_to_steady_state(
    model:       ASM1Model,
    c_in:        np.ndarray,
    volume:      float,
    flowrate_m3h: float,
    do_setpoint: float,
) -> np.ndarray:
    """
    Simule le CSTR jusqu'à l'état quasi-stationnaire.

    Returns:
        np.ndarray : concentrations à l'état quasi-stationnaire
    """
    hrt_h = volume / flowrate_m3h           # heures
    dilution = 1.0 / (hrt_h / 24.0)        # j⁻¹

    oxygen_idx = model.COMPONENT_INDICES['so']

    # État initial : valeurs typiques d'un bassin en fonctionnement
    c = model.dict_to_concentrations({
        'si': 30.0, 'ss': 5.0, 'xi': 25.0, 'xs': 100.0,
        'xbh': 2500.0, 'xba': 150.0, 'xp': 450.0,
        'so': do_setpoint, 'sno': 5.0, 'snh': 2.0,
        'snd': 1.0, 'xnd': 5.0, 'salk': 7.0,
    })

    for _ in range(N_STEPS):
        c = CSTRSolver.solve_step(
            c=c,
            c_in=c_in,
            reaction_func=model.derivatives,
            dt=DT_DAYS,
            dilution_rate=dilution,
            method='rk4',
            oxygen_idx=oxygen_idx,
            do_setpoint=do_setpoint,
        )
        c = np.clip(c, 0.0, None)  # concentrations positives

    return c


def _extract_features_targets(
    scenario: dict,
    c_in:     np.ndarray,
    c_out:    np.ndarray,
    model:    ASM1Model,
) -> dict | None:
    """
    Calcule les features et targets à partir d'un scénario simulé.
    Retourne None si le scénario est invalide (washout total, etc.).
    """
    idx = model.COMPONENT_INDICES

    flowrate  = scenario['flowrate']
    volume    = scenario['volume']
    hrt_hours = volume / flowrate
    srt_days  = volume / (scenario['waste_ratio'] * flowrate * 24.0)

    # --- Influent ---
    cod_in  = scenario['cod']
    tss_in  = scenario['tss']
    nh4_in  = c_in[idx['snh']]
    no3_in  = c_in[idx['sno']]

    # --- Effluent (état quasi-stationnaire) ---
    si_out  = c_out[idx['si']]
    ss_out  = c_out[idx['ss']]
    cod_out = si_out + ss_out          # DCO soluble effluent

    xbh_out = c_out[idx['xbh']]
    xba_out = c_out[idx['xba']]
    xp_out  = c_out[idx['xp']]
    xi_out  = c_out[idx['xi']]
    xs_out  = c_out[idx['xs']]
    tss_out = xbh_out + xba_out + xp_out + xi_out + xs_out

    nh4_out     = c_out[idx['snh']]
    no3_out     = c_out[idx['sno']]
    biomass_out = xbh_out + xba_out

    cod_removal = max(0.0, (cod_in - cod_out) / cod_in * 100.0) if cod_in > 0 else 0.0

    # Filtre les scénarios physiquement impossibles ou numériquement instables
    # (explosion numérique quand SRT très long + cinétiques raides)
    if biomass_out < 10.0:
        return None  # washout total
    if tss_out > 20_000.0 or nh4_out > 200.0 or cod_out > cod_in:
        return None  # valeurs hors plage physique réaliste

    return {
        # Features
        'flowrate':    flowrate,
        'temperature': scenario['temperature'],
        'volume':      volume,
        'cod_in':      cod_in,
        'tss_in':      tss_in,
        'nh4_in':      nh4_in,
        'no3_in':      no3_in,
        'po4_in':      0.0,           # ASM1 ne modélise pas le phosphore
        'hrt_hours':   hrt_hours,
        'srt_days':    srt_days,
        # Targets
        'cod':         cod_out,
        'tss':         tss_out,
        'nh4':         nh4_out,
        'no3':         no3_out,
        'po4':         0.0,
        'biomass':     biomass_out,
        'cod_removal': cod_removal,
    }


def generate(n: int, output: Path, seed: int) -> None:
    rng = np.random.default_rng(seed)
    model = ASM1Model()

    scenarios = _sample_scenarios(n * 2, rng)  # sur-échantillonnage pour compenser les washouts

    records = []
    skipped = 0

    for i, s in enumerate(scenarios):
        if len(records) >= n:
            break

        # Fractionne l'influent en composants ASM1
        components = ASM1Fraction.fractionate(
            cod=s['cod'],
            tss=s['tss'],
            tkn=s['tkn'],
            nh4=s['nh4'],
            no3=s['no3'],
        )
        c_in = model.dict_to_concentrations(components)
        c_in = np.clip(c_in, 0.0, None)

        c_out = _run_to_steady_state(
            model=model,
            c_in=c_in,
            volume=s['volume'],
            flowrate_m3h=s['flowrate'],
            do_setpoint=s['do_setpoint'],
        )

        row = _extract_features_targets(s, c_in, c_out, model)
        if row is None:
            skipped += 1
            continue

        records.append(row)

        if (i + 1) % 100 == 0:
            print(f"  {len(records)}/{n} scénarios valides ({skipped} washouts filtrés)...")

    df = pd.DataFrame(records)
    output.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output, index=False)

    print(f"\nFichier généré : {output}")
    print(f"  Lignes      : {len(df)}")
    print(f"  Washouts    : {skipped}")
    print(f"  Colonnes    : {list(df.columns)}")
    print(f"\nAperçu statistiques :")
    print(df[['cod', 'tss', 'nh4', 'no3', 'biomass', 'cod_removal']].describe().to_string())


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Génère un dataset d\'entraînement ML via simulations ASM1'
    )
    parser.add_argument('--n',      type=int,  default=1000,
                        help='Nombre de scénarios valides à générer (défaut: 1000)')
    parser.add_argument('--output', type=str,  default='data/processed/asm1_training_data.csv',
                        help='Chemin de sortie du CSV')
    parser.add_argument('--seed',   type=int,  default=42,
                        help='Graine aléatoire pour la reproductibilité')
    args = parser.parse_args()

    output_path = ROOT / args.output
    print(f"Génération de {args.n} scénarios (seed={args.seed})...")
    generate(n=args.n, output=output_path, seed=args.seed)
