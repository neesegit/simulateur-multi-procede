"""
Procédé de boues activées avec support pour prédiction RNN

Extension d'ActivatedSludgeProcess permettant d'utiliser un modèle RNN
pour prédire l'évolution des paramètres au lieu d'utiliser les modèles ASM
"""
import logging
import numpy as np

from typing import Dict, Any, Optional
from pathlib import Path

from processes.sludge_process.activated_sludge_process import ActivatedSludgeProcess
from models.rnn.rnn_model import RNNModel
from models.rnn.data_processor import RNNDataProcessor
from models.rnn.predictor import RNNPredictor

logger = logging.getLogger(__name__)

class RNNActivatedSludgeProcess(ActivatedSludgeProcess):
    """
    Procédé de boues activées utilisant un RNN pour la prédiction

    Hérite d'ActivatedSludgeProcess mais remplace la simulation ASM 
    par des prédictions RNN basées sur l'historique
    """

    def __init__(
            self,
            node_id: str,
            name: str,
            config: Dict[str, Any],
            rnn_model_path: Optional[Path] = None,
            rnn_processor_path: Optional[Path] = None,
            use_hybrid_mode: bool = False
    ):
        """
        Initialise le procédé avec support RNN

        Args:
            node_id (str): Identifiant unique
            name (str): Nom descriptif 
            config (Dict[str, Any]): Configuration du procédé
            rnn_model_path (Optional[Path], optional): Chemin vers le modèle RNN entraîné. Defaults to None.
            rnn_processor_path (Optional[Path], optional): Chemin vers le processeur de données. Defaults to None.
            use_hybrid_mode (bool, optional): Si True, utilise le RNN + ASM, sinon RNN seul. Defaults to False.
        """
        super().__init__(node_id, name, config)

        self.use_rnn = rnn_model_path is not None
        self.use_hybride_mode = use_hybrid_mode

        self.rnn_model: Optional[RNNModel] = None
        self.rnn_processor: Optional[RNNDataProcessor] = None
        self.rnn_predictor: Optional[RNNPredictor] = None

        if self.use_rnn and rnn_model_path:
            self._load_rnn(rnn_model_path, rnn_processor_path)

        self.feature_names = self._get_feature_names()
        self.target_names = self._get_target_names()

        logger.info(
            f"RNNActivatedSludgeProcess initialisé : use_rnn={self.use_rnn}, "
            f"hybrid_mode={use_hybrid_mode}"
        )
    
    def _load_rnn(
            self,
            model_path: Path,
            processor_path: Optional[Path]
    ) -> None:
        """Charge le modèle RNN et le processeur"""
        try:
            self.rnn_model = RNNModel.load(model_path)
            logger.info(f"Modèle RNN chargé : {model_path}")

            if processor_path and processor_path.exists():
                self.rnn_processor = RNNDataProcessor.load(processor_path)
                logger.info(f"Processeur RNN chargé : {processor_path}")
            else:
                logger.warning("Processeur RNN non trouvé, création d'un nouveau")
                self.rnn_processor = RNNDataProcessor(
                    seq_len=self.rnn_model.seq_len
                )

        except Exception as e:
            logger.error(f"Erreur lors du chargement du RNN : {e}")
            self.use_rnn = False
            raise

    def _get_feature_names(self) -> list:
        """
        Définit les features d'entrée pour le RNN

        Returns:
            list: Liste des noms de features
        """
        operational = [
            'flowrate',
            'temperature',
            'volume',
            'hrt_hours',
            'srt_days'
        ]

        measured = [
            'cod',
            'ss',
            'nh4',
            'no3',
            'po4',
            'tkn'
        ]

        model_components = []

        try:
            if hasattr(self, 'model_instance') and self.model_instance:
                model_components = self.model_instance.get_component_names()[:5]
        except Exception as e:
            logger.error(f"Problème lors de la récupération des composants du modèle : {e}")
            pass
        
        return operational + measured + model_components
    
    def _get_target_names(self) -> list:
        """
        Définit les cibles à prédire

        Returns:
            list: Liste des noms de cibles
        """
        return [
            'cod',
            'cod_soluble',
            'ss',
            'biomass_concentration',
            'nh4',
            'no3',
            'po4'
        ]
    
    def initialize(self) -> None:
        """Initialise le procédé et le prédicteur RNN"""
        super().initialize()

        if self.use_rnn and self.rnn_model and self.rnn_processor:
            self.rnn_predictor = RNNPredictor(
                model=self.rnn_model,
                processor=self.rnn_processor,
                feature_names=self.feature_names,
                target_names=self.target_names
            )
            logger.info("RNNPredictor initialisé")

    def _extract_features(
            self,
            inputs: Dict[str, Any],
            outputs: Dict[str, Any]
    ) -> Dict[str, float]:
        """
        Extrait les features pour le RNN depuis les inputs/outputs actuels

        Args:
            inputs (Dict[str, Any]): Données d'entrée du pas de temps
            outputs (Dict[str, Any]): Sorties du modèle ASM (si disponibles)

        Returns:
            Dict[str, float]: Dictionnaire de features
        """
        features = {}

        features['flowrate'] = inputs.get('flowrate', 0.0)
        features['temperature'] = inputs.get('temperature', 20.0)
        features['volume'] = self.volume
        features['hrt_hours'] = outputs.get('hrt_hours', 0.0)
        features['srt_days'] = outputs.get('srt_days', 0.0)

        flow = inputs.get('flow')
        if flow:
            features['cod'] = flow.cod
            features['ss'] = flow.ss
            features['nh4'] = flow.nh4
            features['no3'] = flow.no3
            features['po4'] = flow.po4
            features['tkn'] = flow.tkn

        components = inputs.get('components', {})

        for name in self.feature_names:
            if name not in features and name in components:
                features[name] = components[name]

        return features
    
    def _predict_with_rnn(
            self,
            features: Dict[str, float]
    ) -> Optional[Dict[str, float]]:
        """
        Effectue une prédiction avec le RNN

        Args:
            features (Dict[str, float]): Features d'entrée

        Returns:
            Optional[Dict[str, float]]: Prédictions ou None si impossible
        """
        if not self.rnn_predictor:
            return None
        
        self.rnn_predictor.update_buffer(features)

        if self.rnn_predictor.can_predict():
            predictions = self.rnn_predictor.predict()
            logger.debug(f"Predictions RNN : {predictions}")
            return predictions
        else:
            logger.debug("Buffer RNN insuffisant, attente de plus de données")
            return None
        
    def _merge_predictions(
            self,
            asm_outputs: Dict[str, Any],
            rnn_predictions: Dict[str, float],
            alpha: float = 0.5
    ) -> Dict[str, Any]:
        """
        Fusionne les prédictions ASM et RNN en mode hybride

        Args:
            asm_outputs (Dict[str, Any]): Sorties du modèle ASM
            rnn_predictions (Dict[str, float]): Prédictions du RNN
            alpha (float, optional): Poids du RNN (1-alpha pour ASM). Defaults to 0.5.

        Returns:
            Dict[str, Any]: Sorties fusionnées
        """
        merged = asm_outputs.copy()

        for target_name, rnn_value in rnn_predictions.items():
            if target_name in asm_outputs:
                asm_value = asm_outputs[target_name]

                merged[target_name] = alpha * rnn_value + (1 - alpha) * asm_value

                logger.debug(
                    f"{target_name}: ASM={asm_value:.2f}, RNN={rnn_value:.2f}, "
                    f"Fusionné={merged[target_name]:.2f}"
                )
        return merged
    
    def process(self, inputs: Dict[str, Any], dt: float) -> Dict[str, Any]:
        """
        Traite un pas de temps avec RNN ou mode hybride

        Args:
            inputs (Dict[str, Any]): Données d'entrée
            dt (float): Pas de temps (jours)

        Returns:
            Dict[str, Any]: Sorties du procédé
        """
        asm_outputs = super().process(inputs, dt)

        if not self.use_rnn:
            return asm_outputs
        
        features = self._extract_features(inputs, asm_outputs)

        rnn_predictions = self._predict_with_rnn(features)
        if rnn_predictions is None:
            logger.debug("Utilisation de la sortie ASM (buffer RNN insuffisant)")
            return asm_outputs
        
        if self.use_hybride_mode:
            logger.debug("Mode hybride : fusion ASM + RNN")
            final_outputs = self._merge_predictions(
                asm_outputs,
                rnn_predictions,
                alpha=0.7
            )
        else:
            logger.debug("Mode RNN pur : remplacement des sorties ASM")
            final_outputs = asm_outputs.copy()
            final_outputs.update(rnn_predictions)

        final_outputs['prediction_mode'] = 'hybrid' if self.use_hybride_mode else 'rnn'
        return final_outputs