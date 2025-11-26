import logging
import numpy as np

from typing import Dict, Any, Optional
from pathlib import Path

from keras.models import Sequential, load_model
from keras.layers import LSTM, Dense, Dropout
from keras.callbacks import EarlyStopping, ModelCheckpoint

logger = logging.getLogger(__name__)

class RNNModel:
    """
    Modèle RNN (LSTM) pour la prédiction de séries temporelles
    """
    
    def __init__(
            self, 
            input_dim: int, 
            output_dim: int, 
            seq_len: int = 7,
            hidden_units: int = 64,
            dropout_rate: float = 0.2,
            num_layers: int = 1
    ):
        """
        Initialise le modèle RNN

        Args:
            input_dim (int): Nombre de features d'entrée
            output_dim (int): Nombre de sorties à prédire
            seq_len (int, optional): Longueur des séquences. Defaults to 7.
            hidden_units (int, optional): Nombre d'unités dans les couches LSTM. Defaults to 64.
            dropout_rate (float, optional): Taux de dropout pour régularisation. Defaults to 0.2.
            num_layers (int, optional): Nombre de couches LSTM. Defaults to 1.
        """
        self.input_dim = input_dim
        self.output_dim = output_dim
        self.seq_len = seq_len
        self.hidden_units = hidden_units
        self.dropout_rate = dropout_rate
        self.num_layers = num_layers

        self.model = self._build_model()

        logger.info(
            f"RNNModel créé : input_dim={input_dim}, output_dim={output_dim}, "
            f"sequence_length={seq_len}, hidden_units={hidden_units}, "
            f"num_layers={num_layers}"
        )

    def _build_model(self) -> Sequential:
        """Construit l'architecture du modèle"""
        model = Sequential()

        if self.num_layers > 1:
            model.add(LSTM(
                self.hidden_units,
                input_shape=(self.seq_len, self.input_dim),
                return_sequences=True
            ))
            model.add(Dropout(self.dropout_rate))

            for _ in range(self.num_layers - 2):
                model.add(LSTM(self.hidden_units, return_sequences=True))
                model.add(Dropout(self.dropout_rate))

            model.add(LSTM(self.hidden_units))
            model.add(Dropout(self.dropout_rate))

        else:
            model.add(LSTM(
                self.hidden_units,
                input_shape=(self.seq_len, self.input_dim)
            ))
            model.add(Dropout(self.dropout_rate))
        
        model.add(Dense(self.output_dim))

        model.compile(
            optimizer='adam',
            loss='mse',
            metrics=['mae']
        )
        return model

    def fit(
            self,
            X: np.ndarray,
            y: np.ndarray,
            validation_split: float = 0.2,
            epochs: int = 100,
            batch_size: int = 32,
            early_stopping_patience: int = 10,
            checkpoint_path: Optional[Path] = None,
            verbose: int = 1
    ) -> Dict[str, Any]:
        """
        Entraîne le modèle

        Args:
            X (np.ndarray): Séquences d'entrée (n_sequences, sequence_length, n_features)
            y (np.ndarray): Cibles (n_sequences, n_targets)
            validation_split (float, optional): Fraction des données pour validation. Defaults to 0.2.
            epochs (int, optional): Nombre d'époques maximum. Defaults to 100.
            batch_size (int, optional): Taille des batchs. Defaults to 32.
            early_stopping_patience (int, optional): Patience pour early stopping. Defaults to 10.
            checkpoint_path (Optional[Path], optional): Chemin pour sauvegarder le meilleur modèle. Defaults to None.
            verbose (int, optional): Niveau de verbosité. Defaults to 1.

        Returns:
            Dict[str, Any]: Historique d'entrainement
        """
        callbacks = []

        early_stop = EarlyStopping(
            monitor='val_loss',
            patience=early_stopping_patience,
            restore_best_weights=True,
            verbose=verbose
        )
        callbacks.append(early_stop)

        if checkpoint_path:
            checkpoint_path.parent.mkdir(parents=True, exist_ok=True)
            checkpoint = ModelCheckpoint(
                str(checkpoint_path),
                monitor='val_loss',
                save_best_only=True,
                verbose=verbose
            )
            callbacks.append(checkpoint)

        logger.info(
            f"Début de l'entraînement : {X.shape[0]} séquences, "
            f"{epochs} époques max, batch_size={batch_size}"
        )

        history = self.model.fit(
            X, y,
            validation_split=validation_split,
            epochs=epochs,
            batch_size=batch_size,
            callbacks=callbacks,
            verbose=str(verbose)
        )

        logger.info("Entraînement terminé")

        return history.history
    
    def predict(self, X: np.ndarray) -> np.ndarray:
        """
        Prédit les valeurs

        Args:
            X (np.ndarray): Séquences d'entrée (n_sequences, sequence_length, n_features)

        Returns:
            np.ndarray: Prédictions (n_sequences, n_targets)
        """
        return self.model.predict(X, verbose='0')
    
    def evaluate(
            self,
            X: np.ndarray,
            y: np.ndarray
    ) -> Dict[str, float]:
        """
        Evalue le modèle

        Args:
            X (np.ndarray): Séquences d'entrée
            y (np.ndarray): Cibles

        Returns:
            Dict[str, float]: Dictionnaire des métriques
        """
        loss, mae = self.model.evaluate(X, y, verbose='0')

        metrics = {
            'loss': loss,
            'mae': mae
        }

        logger.info(f"Evaluation : loss={loss:.4f}, mae={mae:.4f}")

        return metrics
    
    def save(self, path: Path) -> None:
        """Sauvegarde le modèle"""
        path.parent.mkdir(parents=True, exist_ok=True)
        self.model.save(str(path))
        logger.info(f"Modèle sauvegardé : {path}")

    @classmethod
    def load(cls, path: Path) -> 'RNNModel':
        """Charge un modèle sauvegardé"""
        model_keras = load_model(str(path))

        input_shape = model_keras.input_shape
        output_shape = model_keras.output_shape

        instance = cls.__new__(cls)
        instance.model = model_keras
        instance.seq_len = input_shape[1]
        instance.input_dim = input_shape[2]
        instance.output_dim = output_shape[1]

        logger.info(f"Modèle chargé : {path}")
        return instance