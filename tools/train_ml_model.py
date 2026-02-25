"""
Entraîne un modèle ML (LinearModel ou RandomForestModel) depuis un CSV
et sauvegarde le modèle entraîné au format pickle.

Le fichier produit est directement utilisable dans la config de simulation
via le paramètre "model_path".

Ce script est ISOLÉ du reste de la simulation — il ne sera plus nécessaire
quand des données réelles seront disponibles (remplacer juste le CSV d'entrée).

Usage :
    # Depuis un CSV généré par generate_training_data.py
    python tools/train_ml_model.py --model LinearModel
    python tools/train_ml_model.py --model RandomForestModel

    # Avec options
    python tools/train_ml_model.py \\
        --model RandomForestModel \\
        --data data/processed/asm1_training_data.csv \\
        --output models/trained/random_forest.pkl \\
        --test-size 0.2

    # Avec vrais données (même format de colonnes)
    python tools/train_ml_model.py \\
        --model LinearModel \\
        --data data/processed/real_wwtp_data.csv
"""
import sys
import argparse
import logging
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split

from models.ml.linear_model import LinearModel
from models.ml.random_forest_model import RandomForestModel

logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger(__name__)

AVAILABLE_MODELS = {
    'LinearModel':       LinearModel,
    'RandomForestModel': RandomForestModel,
}

FEATURE_COLS = [
    'flowrate', 'temperature', 'volume',
    'cod_in', 'tss_in', 'nh4_in', 'no3_in', 'po4_in',
    'hrt_hours', 'srt_days',
]
TARGET_COLS = [
    'cod', 'tss', 'nh4', 'no3', 'po4',
    'biomass', 'cod_removal',
]

DEFAULT_DATA   = ROOT / 'data/processed/asm1_training_data.csv'
DEFAULT_OUTPUT = ROOT / 'models/trained/{model}.pkl'


def train(model_name: str, data_path: Path, output_path: Path, test_size: float) -> None:
    # --- Chargement ---
    if not data_path.exists():
        print(f"Erreur : fichier de données introuvable : {data_path}")
        print("Générez-le d'abord avec : python tools/generate_training_data.py")
        sys.exit(1)

    df = pd.read_csv(data_path)
    print(f"Données chargées : {len(df)} lignes depuis {data_path}")

    missing_features = [c for c in FEATURE_COLS if c not in df.columns]
    missing_targets  = [c for c in TARGET_COLS  if c not in df.columns]
    if missing_features or missing_targets:
        print(f"Erreur : colonnes manquantes — features: {missing_features}, targets: {missing_targets}")
        sys.exit(1)

    X = df[FEATURE_COLS].to_numpy(dtype=float)
    y = df[TARGET_COLS].to_numpy(dtype=float)

    # --- Split train/test ---
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=test_size, random_state=42
    )
    print(f"Split : {len(X_train)} train / {len(X_test)} test")

    # --- Entraînement ---
    model_class = AVAILABLE_MODELS[model_name]
    model = model_class()

    print(f"Entraînement {model_name}...")
    metrics = model.fit(X_train, y_train)

    # --- Évaluation sur le jeu de test ---
    X_test_scaled = model.scaler.transform(X_test)
    r2_test = model.model.score(X_test_scaled, y_test)

    print(f"\nRésultats :")
    print(f"  R² train : {metrics.get('r2_score', '—'):.4f}")
    print(f"  R² test  : {r2_test:.4f}")

    if 'feature_importances' in metrics:
        importances = metrics['feature_importances']
        print(f"\n  Importances features (top 5) :")
        ranked = sorted(zip(FEATURE_COLS, importances), key=lambda x: x[1], reverse=True)
        for name, imp in ranked[:5]:
            print(f"    {name:<15} {imp:.3f}")

    # --- Sauvegarde ---
    output_path.parent.mkdir(parents=True, exist_ok=True)
    model.save(str(output_path))
    print(f"\nModèle sauvegardé : {output_path}")
    print(f"\nPour l'utiliser dans une config de simulation :")
    print(f'  "model_path": "{output_path.relative_to(ROOT)}"')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Entraîne un modèle ML depuis un CSV et sauvegarde le pickle'
    )
    parser.add_argument(
        '--model', type=str, required=True,
        choices=list(AVAILABLE_MODELS.keys()),
        help='Modèle à entraîner'
    )
    parser.add_argument(
        '--data', type=str,
        default=str(DEFAULT_DATA),
        help=f'Chemin vers le CSV d\'entraînement (défaut: {DEFAULT_DATA})'
    )
    parser.add_argument(
        '--output', type=str, default=None,
        help='Chemin de sortie du pickle (défaut: models/trained/<model>.pkl)'
    )
    parser.add_argument(
        '--test-size', type=float, default=0.2,
        help='Fraction du jeu de test (défaut: 0.2)'
    )
    args = parser.parse_args()

    output = Path(args.output) if args.output else Path(
        str(DEFAULT_OUTPUT).format(model=args.model.lower().replace('model', ''))
    )

    train(
        model_name=args.model,
        data_path=Path(args.data),
        output_path=output,
        test_size=args.test_size,
    )
