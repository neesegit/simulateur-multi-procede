import logging
import numpy as np

from typing import List, Dict, Optional

from models.rnn.rnn_model import RNNModel
from models.rnn.data_processor import RNNDataProcessor

logger = logging.getLogger(__name__)

class RNNPredictor:
    """
    Prédicteur en temps réel utilisant un buffer de séquences
    """

    def __init__(
            self,
            model: RNNModel,
            processor: RNNDataProcessor,
            feature_names: List[str],
            target_names: List[str]
    ):
        """
        Initialise le prédicteur

        Args:
            model (RNNModel): Modèle RNN entraîné
            processor (RNNDataProcessor): Processeur de données
            feature_names (List[str]): Noms des features d'entrée
            target_names (List[str]): Noms des cibles à prédire
        """
        self.model = model
        self.processor = processor
        self.feature_names = feature_names
        self.target_names = target_names

        self.buffer: List[np.ndarray] = []
        self.seq_len = processor.seq_len

        logger.info(
            f"RNNPredictor initialisé : {len(feature_names)} features, "
            f"{len(target_names)} targets, buffer_size={self.seq_len}"
        )

    def update_buffer(self, new_input: Dict[str, float]) -> None:
        """
        Ajoute une nouvelle observation au buffer

        Args:
            new_input (Dict[str, float]): Dictionnaire {feature_name: value}
        """
        features = np.array([new_input.get(name, 0.0) for name in self.feature_names])

        scaled = self.processor.transform(features.reshape(1, -1))[0]

        self.buffer.append(scaled)

        if len(self.buffer) > self.seq_len:
            self.buffer.pop(0)
        
        logger.debug(f"Buffer mis à jour : {len(self.buffer)}/{self.seq_len}")

    def can_predict(self) -> bool:
        """Vérifie si le buffer est suffisamment rempli pour prédire"""
        return len(self.buffer) >= self.seq_len
    
    def predict(self) -> Optional[Dict[str, float]]:
        """
        Prédit les valeurs à partir du buffer actuel

        Returns:
            Optional[Dict[str, float]]: Dictionnaire {target_name: predicted_value} ou None si buffer insuffisant
        """
        if not self.can_predict():
            logger.warning(
                f"Buffer insuffisant : {len(self.buffer)}/{self.seq_len}"
            )
            return None
        
        sequence = np.array([self.buffer])

        predictions = self.model.predict(sequence)[0]

        result = {
            name: float(value)
            for name, value in zip(self.target_names, predictions)
        }

        logger.debug(f"Prédiction effectuée : {result}")

        return result
    
    def reset(self) -> None:
        """Vide le buffer"""
        self.buffer.clear()
        logger.debug("Buffer réinitialisé")