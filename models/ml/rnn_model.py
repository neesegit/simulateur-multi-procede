"""
Modèle RNN intégré dans le framework
"""
import numpy as np
import logging
import pickle

from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from sklearn.preprocessing import StandardScaler

from keras.models import Sequential, Model
from keras.layers import LSTM, Dense, Dropout

from keras.saving import load_model

from models.ml_model import MLModel

logger = logging.getLogger(__name__)

class RNNModel(MLModel):
    """Modèle RNN pour prédiction de procédés de traitement"""

    def __init__(self, params: Optional[Dict[str, Any]] = None):
        super().__init__(params)

        self.sequence_length = self.params.get('sequence_length', 7)
        self.hidden_units = self.params.get('hidden_units', 64)
        self.num_layers = self.params.get('num_layers', 1)
        self.dropout = self.params.get('dropout', 0.2)

        self.model: Any
        self.scaler = StandardScaler()
        self.sequence_buffer = []

        logger.info(
            f"RNNModel initialisé : seq_len={self.sequence_length}, "
            f"features={len(self.feature_names)}, targets={len(self.target_names)}"
        )

    def _get_default_features(self) -> List[str]:
        """Features par défaut pour le RNN"""
        return [
            'flowrate', 'temperature', 'volume',
            'cod_in', 'ss_in', 'nh4_in', 'no3_in', 'po4_in',
            'cod', 'ss', 'nh4', 'no3', 'po4',
            'biomass', 'hrt_hours'
        ]
    
    def _get_default_targets(self) -> List[str]:
        """Targets par défaut"""
        return [
            'cod', 'ss', 'nh4', 'no3', 'po4',
            'biomass', 'cod_removal'
        ]
    
    @property
    def model_type(self) -> str:
        return "RNN"
    
    def get_component_names(self) -> List[str]:
        return self.target_names
    
    def _build_model(self, input_dim: int, output_dim: int) -> Sequential:
        """Construit l'architecture du réseau"""
        model = Sequential()

        if self.num_layers > 1:
            model.add(
                LSTM(
                    self.hidden_units,
                    input_shape=(self.sequence_length, input_dim),
                    return_sequences=True
                )
            )
            model.add(Dropout(self.dropout))

            for _ in range(self.num_layers - 2):
                model.add(LSTM(self.hidden_units, return_sequences=True))
                model.add(Dropout(self.dropout))

            model.add(LSTM(self.hidden_units))
            model.add(Dropout(self.dropout))
        else:
            model.add(
                LSTM(
                    self.hidden_units,
                    input_shape=(self.sequence_length, input_dim)
                )
            )
            model.add(Dropout(self.dropout))
        
        model.add(Dense(output_dim))
        model.compile(optimizer='adam', loss='mse', metrics=['mae'])

        return model
    
    def fit(
        self, 
        X: np.ndarray, 
        y: np.ndarray,
        validation_split: float = 0.2,
        epochs: int = 100,
        batch_size: int = 32
    ) -> Dict[str, Any]:
        """
        Entraîne le modèle RNN

        Args:
            X (np.ndarray): Features (n_samples, n_features)
            y (np.ndarray): Targets (n_samples, n_targets)
            validation_split (float, optional): Defaults to 0.2.
            epochs (int, optional): Defaults to 100.
            batch_size (int, optional): Defaults to 32.
        """
        logger.info(f"Début entraînement RNN : {X.shape[0]} échantillons")

        X_scaled = self.scaler.fit_transform(X)

        X_seq, y_seq = self._create_sequences(X_scaled, y)

        self.model = self._build_model(X_seq.shape[2], y_seq.shape[1])

        history = self.model.fit(
            X_seq, y_seq,
            validation_split=validation_split,
            epochs=epochs,
            batch_size=batch_size,
            verbose="1"
        )

        self.is_fitted = True
        logger.info("Entraînement terminé")

        return history.history

    def _create_sequences(self, X: np.ndarray, y: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        """Crée des séquences temporelles"""
        X_seq, y_seq = [], []

        for i in range(len(X) - self.sequence_length):
            X_seq.append(X[i:i + self.sequence_length])
            y_seq.append(y[i+self.sequence_length])

        return np.array(X_seq), np.ndarray(y_seq)
    
    def predict_step(
            self,
            current_state: Dict[str, float],
            inputs: Dict[str, float],
            dt: float
    ) -> Dict[str, Any]:
        """Prédit le prochain état"""
        if not self.is_fitted:
            raise ValueError("Modèole non entraîné. Utilisez .fit() ou .load()")
        
        features = self._extract_features(current_state, inputs)

        self.update_buffer(features)

        if len(self.sequence_buffer) < self.sequence_length:
            logger.warning(f"Buffer insuffisant ({len(self.sequence_buffer)}/{self.sequence_length})")
            return current_state
        
        sequence = np.array(self.sequence_buffer[-self.sequence_length:])
        sequence_scaled = self.scaler.transform(sequence)

        X = sequence_scaled.reshape(1, self.sequence_length, -1)

        predictions = self.model.predict(X, verbose="0")[0]

        result: Dict[str, Any] = {name: float(pred) for name, pred in zip(self.target_names, predictions)}

        result['cod_removal'] = self._compute_cod_removal(result, inputs)
        result['flowrate'] = inputs.get('flowrate', 0)
        result['temperature'] = inputs.get('temperature', 20)
        result['model_type'] = 'RNN'

        return result

    def _compute_cod_removal(self, state: Dict[str, float], inputs: Dict[str, float]) -> float:
        """Calcule le taux d'élimination de la DCO"""
        cod_in = inputs.get('cod_in', 0)
        cod_out = state.get('cod', 0)
        if cod_in > 0:
            return ((cod_in - cod_out)/cod_in) * 100
        return 0.0
    
    def initialize_state(self, initial_conditions: Dict[str, float]) -> Dict[str, float]:
        """Initialise l'état du modèle"""
        state = {target: 0.0 for target in self.target_names}
        state.update(initial_conditions)

        self.sequence_buffer = []

        return state
    
    def save(self, path: str) -> None:
        """Sauvegarde le modèle complet"""
        save_path = Path(path)
        save_path.parent.mkdir(parents=True, exist_ok=True)

        model_path = save_path.parent / f"{save_path.stem}.keras"
        self.model.save(str(model_path))

        metadata = {
            'scaler': self.scaler,
            'feature_names': self.feature_names,
            'target_names': self.target_names,
            'sequence_length': self.sequence_length,
            'params': self.params
        }

        with open(path, 'wb') as f:
            pickle.dump(metadata, f)

        logger.info(f"Modèle RNN sauvegardé : {path}")

    def load(self, path: str) -> None:
        """Charge un modle pré-entrainé"""
        load_path = Path(path)

        model_path = load_path.parent / f"{load_path.stem}.keras"
        self.model = load_model(str(model_path))

        with open(load_path, 'rb') as f:
            metadata = pickle.load(f)

        self.scaler = metadata['scaler']
        self.feature_names = metadata['feature_names']
        self.target_names = metadata['target_names']
        self.sequence_length = metadata['sequence_length']
        self.params.update(metadata.get('params', {}))
        
        self.is_fitted = True
        self.sequence_buffer = []

        logger.info(f"Modèle RNN chargé : {path}")