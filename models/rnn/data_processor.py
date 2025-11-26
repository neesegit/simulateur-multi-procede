import logging
import numpy as np
import pickle

from pathlib import Path
from typing import Tuple
from sklearn.preprocessing import MinMaxScaler

logger = logging.getLogger(__name__)

class RNNDataProcessor:
    """
    Processeur de données pour le RNN

    Gère la normalisation et la création de séquences temporelles
    """

    def __init__(self, seq_len: int = 7):
        """
        Initialise le processeur

        Args:
            seq_len (int, optional): Nombre de pas de temps dans chaque séquence. Defaults to 7.
        """
        self.seq_len = seq_len
        self.scaler = MinMaxScaler(feature_range=(0,1))
        self.is_fitted = False

        logger.info(f"RNNDataProcessor initialisé avec sequence_length={seq_len}")

    def fit_trasnform(self, X: np.ndarray) -> np.ndarray:
        """
        Ajuste le scaler et transforme les données

        Args:
            X (np.ndarray): Donnée d'entrée (n_samples, n_features)

        Returns:
            np.ndarray: Donnée normalisées
        """
        if X.shape[0] < self.seq_len:
            raise ValueError(
                f"Pas asez de données : {X.shape[0]} échantillons, "
                f"minimum {self.seq_len} requis"
            )

        X_scaled = self.scaler.fit_transform(X)
        self.is_fitted = True

        logger.debug(f"Scaler ajusté sur {X.shape[0]} échantillons, {X.shape[1]} features")
        return X_scaled
    
    def transform(self, X: np.ndarray) -> np.ndarray:
        """
        Transforme les données avec le scaler déjà ajusté

        Args:
            X (np.ndarray): Données d'entrée

        Returns:
            np.ndarray: Données normalisées

        Raises:
            ValuesError: Si le scaler n'est pas ajusté
        """
        if not self.is_fitted:
            raise ValueError("Le scaler doit être ajusté avant la transformation")
        return self.scaler.transform(X)
    
    def inverse_transform(self, X_scaled: np.ndarray) -> np.ndarray:
        """
        Inverse la transformation pour obtenir les valeurs originales

        Args:
            X_scaled (np.ndarray): Données normalisées

        Returns:
            np.ndarray: Données dans l'échelle originale
        """
        return self.scaler.inverse_transform(X_scaled)
    
    def create_sequences(
            self,
            X: np.ndarray,
            y: np.ndarray
    ) -> Tuple[np.ndarray, np.ndarray]:
        """
        Crée des séquences temporelles pour l'entraînement

        Args:
            X (np.ndarray): Features (n_samples, n_features)
            y (np.ndarray): Cibles (n_samples, n_targets)

        Returns:
            Tuple[np.ndarray, np.ndarray]: Tuple (X_sequences, y_targets) où :
                                            - X_sequences: (n_sequences, sequence_length, n_features)
                                            - y_targets: (n_sequences, n_targets)
        """
        X_seq, y_seq = [], []

        for i in range(len(X) - self.seq_len):
            X_seq.append(X[i : i + self.seq_len])
            y_seq.append(y[i+self.seq_len])

        X_seq = np.array(X_seq)
        y_seq = np.array(y_seq)

        logger.debug(
            f"Séquences créées : {X_seq.shape[0]} séquences de longueur "
            f"{X_seq.shape[1]} avec {X_seq.shape[2]} features"
        )
        return X_seq, y_seq
    
    def save(self, path: Path) -> None:
        """Sauvegarde le scaler"""
        path.parent.mkdir(parents=True, exist_ok=True)

        with open(path, 'wb') as f:
            pickle.dump({
                'scaler': self.scaler,
                'sequence_length': self.seq_len,
                'is_fitted': self.is_fitted
            }, f)

            logger.info(f"Processeur sauvegardé : {path}")

    @classmethod
    def load(cls, path: Path) -> 'RNNDataProcessor':
        """Charge un scaler sauvegardé"""

        with open(path, 'rb') as f:
            data = pickle.load(f)

        processor = cls(seq_len=data['sequence_length'])
        processor.scaler = data['scaler']
        processor.is_fitted = data['is_fitted']

        logger.info(f"Processeur chargé : {path}")
        return processor