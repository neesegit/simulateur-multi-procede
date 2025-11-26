import logging
import numpy as np

from typing import List, Tuple, Optional, Any, Dict
from pathlib import Path

from models.rnn.data_processor import RNNDataProcessor
from models.rnn.rnn_model import RNNModel
from models.rnn.predictor import RNNPredictor

logger = logging.getLogger(__name__)

class RNNTrainer:
    """
    Gestionnaire d'entraînement complet pour le RNN
    """

    def __init__(
            self,
            feature_names: List[str],
            target_names: List[str],
            seq_len: int = 7,
            hidden_units: int = 64,
            num_layers: int = 1
    ):
        """
        Initialise le trainer

        Args:
            feature_names (List[str]): Noms des features d'entrée
            target_names (List[str]): Noms des cibles à prédire
            seq_len (int, optional): Longueur des séquences. Defaults to 7.
            hidden_units (int, optional): Unités cachées dans le LSTM. Defaults to 64.
            num_layers (int, optional): Nombre de couches LSTM. Defaults to 1.
        """
        self.feature_names = feature_names
        self.target_names = target_names
        self.seq_len = seq_len
        self.hidden_units = hidden_units
        self.num_layers = num_layers

        self.processor: Optional[RNNDataProcessor] = None
        self.model: Optional[RNNModel] = None

        logger.info(
            f"RNNTrainer initialisé : {len(feature_names)} features, "
            f"{len(target_names)} targets"
        )

    def prepare_data(
            self,
            data: np.ndarray,
            feature_cols: List[int],
            target_cols: List[int]
    ) -> Tuple[np.ndarray, np.ndarray]:
        """
        Prépare les données pour l'entraînement

        Args:
            data (np.ndarray): Données brutes (n_samples, n_total_features)
            feature_cols (List[int]): Indices des colonnes features
            target_cols (List[int]): Indices des colonnes cibles

        Returns:
            Tuple[np.ndarray, np.ndarray]: Tuple (X_sequences, y_targets)
        """
        X = data[:, feature_cols]
        y = data[:, target_cols]

        self.processor = RNNDataProcessor(seq_len=self.seq_len)
        X_scaled = self.processor.fit_trasnform(X)

        X_seq, y_seq = self.processor.create_sequences(X_scaled, y)

        logger.info(
            f"Données préparées : {X_seq.shape[0]} séquences, "
            f"{X_seq.shape[2]} features, {y_seq.shape[1]} targets"
        )

        return X_seq, y_seq
    
    def train(
            self,
            X_seq: np.ndarray,
            y_seq: np.ndarray,
            validation_split: float = 0.2,
            epochs: int = 100,
            batch_size: int = 32,
            model_path: Optional[Path] = None,
            processor_path: Optional[Path] = None
    ) -> Dict[str, Any]:
        """
        Entraîne le modèle

        Args:
            X_seq (np.ndarray): Séquences d'entrée
            y_seq (np.ndarray): Cibles
            validation_split (float, optional): Fraction pour validation. Defaults to 0.2.
            epochs (int, optional): Nombre d'époques. Defaults to 100.
            batch_size (int, optional): Taille des batchs. Defaults to 32.
            model_path (Optional[Path], optional): Chemin pour sauvegarder le modèle. Defaults to None.
            processor_path (Optional[Path], optional): Chemin pour sauvegarder le processeur. Defaults to None.

        Returns:
            Dict[str, Any]: Historique d'entraînement
        """
        if self.processor is None:
            raise ValueError("Les données doivent être préparées avant l'entraînement")
        
        self.model = RNNModel(
            input_dim=X_seq.shape[2],
            output_dim=y_seq.shape[1],
            seq_len=self.seq_len,
            hidden_units=self.hidden_units,
            num_layers=self.num_layers
        )

        history = self.model.fit(
            X_seq, y_seq,
            validation_split=validation_split,
            epochs=epochs,
            batch_size=batch_size,
            checkpoint_path=model_path
        )

        if model_path:
            self.model.save(model_path)

        if processor_path:
            self.processor.save(processor_path)
        
        return history
    
    def create_predictor(self) -> RNNPredictor:
        """
        Crée un prédicteur à partir du modèle entraîné

        Returns:
            RNNPredictor: RNNPredictor prêt à l'emploi
        """
        if self.model is None or self.processor is None:
            raise ValueError("Le modèle doit être entraîné avant de créer un prédicteur")
        
        return RNNPredictor(
            model=self.model,
            processor=self.processor,
            feature_names=self.feature_names,
            target_names=self.target_names
        )