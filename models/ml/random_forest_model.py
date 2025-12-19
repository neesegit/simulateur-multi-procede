"""
Modèle ML baseline : Random Forest
"""

import numpy as np
import logging
import pickle

from pathlib import Path
from typing import Dict, List, Any, Optional
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import RandomForestRegressor

from models.ml_model import MLModel

logger = logging.getLogger(__name__)

class RandomForestModel(MLModel):
    """Modèle Random Forest"""

    def __init__(self, params: Optional[Dict[str, Any]] = None):
        super().__init__(params)

        n_estimators = self.params.get('n_estimators', 100)
        max_depth = self.params.get('max_depth', None)

        self.feature_names = self._get_default_features()
        self.target_names = self._get_default_targets()

        self.model = RandomForestRegressor(
            n_estimators=n_estimators,
            max_depth=max_depth,
            random_state=42
        )
        self.scaler = StandardScaler()

        logger.info(f"RandomForestModel initialisé : n_estimators={n_estimators}")

    def _get_default_features(self) -> List[str]:
        return [
            'flowrate', 'temperature', 'volume',
            'cod_in', 'tss_in', 'nh4_in', 'no3_in', 'po4_in',
            'hrt_hours', 'srt_days'
        ]
    
    def _get_default_targets(self) -> List[str]:
        return [
            'cod', 'tss', 'nh4', 'no3', 'po4',
            'biomass', 'cod_removal'
        ]

    @property
    def model_type(self) -> str:
        return "RandomForest"
    
    def get_component_names(self) -> List[str]:
        return self.target_names
    
    def fit(self, X: np.ndarray[tuple[Any, ...], np.dtype[Any]], y: np.ndarray[tuple[Any, ...], np.dtype[Any]]) -> Dict:
        """Entraîne le Random Forest"""
        logger.info(f"Entraînement RandomForest : {X.shape[0]} échantillons")

        X_scaled = self.scaler.fit_transform(X)
        self.model.fit(X_scaled, y)

        score = self.model.score(X_scaled, y)
        self.is_fitted = True

        logger.info(f"Entrainement terminé : R² = {score:.4f}")
        return {'r2_score': score, 'feature_importances': self.model.feature_importances_}
    
    def predict_step(self, current_state: Dict[str, float], inputs: Dict[str, float], dt: float) -> Dict[str, Any]:
        """Prédit le prochain état"""
        if not self.is_fitted:
            raise ValueError("Modèle non entraîné")
        
        features = self._extract_features(current_state, inputs)
        X = self.scaler.transform(features.reshape(1, -1))

        predictions = self.model.predict(X)[0]

        result: Dict[str, Any] = {name: float(pred) for name, pred in zip(self.target_names, predictions)}
        result['flowrate'] = inputs.get('flowrate', 0)
        result['temperature'] = inputs.get('temperature', 20)
        result['model_type'] = 'RandomForest'

        return result
    
    def initialize_state(self, initial_conditions: Dict[str, float]) -> Dict[str, float]:
        state = {target: 0.0 for target in self.target_names}
        state.update(initial_conditions)
        return state
    
    def save(self, path: str) -> None:
        save_path = Path(path)
        save_path.parent.mkdir(parents=True, exist_ok=True)

        with open(path, 'wb') as f:
            pickle.dump({
                'model': self.model,
                'scaler': self.scaler,
                'feature_names': self.feature_names,
                'target_names': self.target_names
            }, f)

        logger.info(f"RandomForestModel sauvegardé : {path}")

    def load(self, path: str) -> None:
        with open(path, 'rb') as f:
            data = pickle.load(f)

        self.model = data['model']
        self.scaler = data['scaler']
        self.feature_names = data['feature_names']
        self.target_names = data['target_names']
        self.is_fitted = True

        logger.info(f"RandomForestModel chargé : {path}")