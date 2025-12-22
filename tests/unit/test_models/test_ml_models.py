"""
Tests unitaires pour les modèles ML
"""
import pytest
import numpy as np
from unittest.mock import Mock, MagicMock, patch

from models.ml.linear_model import LinearModel
from models.ml.random_forest_model import RandomForestModel

class TestLinearModel:
    """Tests pour LinearModel"""

    def test_initialization(self):
        """Test : initialisation"""
        model = LinearModel()

        assert model is not None
        assert hasattr(model, 'model')
        assert hasattr(model, 'scaler')
        assert hasattr(model, 'feature_names')
        assert hasattr(model, 'target_names')

    def test_model_type(self):
        """Test : model_type"""
        model = LinearModel()

        assert model.model_type == 'Linear'

    def test_get_component_names(self):
        """Test : get_component_names"""
        model = LinearModel()

        names = model.get_component_names()

        assert isinstance(names, list)
        assert len(names) > 0
        assert 'cod' in names

    def test_fit(self, sample_training_data):
        """Test : entraînement"""
        X, y = sample_training_data
        model = LinearModel()

        result = model.fit(X, y)

        assert 'r2_score' in result
        assert model.is_fitted is True

    def test_predict_step_without_training_raises_error(self):
        """Test : prédiction sans entraînement lève une erreur"""
        model = LinearModel()

        current_state = {'cod': 100.0}
        inputs = {'flowrate': 1000.0}

        with pytest.raises(ValueError, match='non entrainé'):
            model.predict_step(current_state, inputs, dt=0.1)

    def test_predict_step_after_training(self, sample_training_data):
        """Test : prédiction après entraînement"""
        X, y = sample_training_data
        model = LinearModel()
        model.fit(X, y)

        current_state = {
            'cod': 100.0,
            'tss': 2000.0,
            'nh4': 2.0
        }
        inputs = {
            'flowrate': 1000.0,
            'temperature': 20.0,
            'cond_in': 500.0
        }

        result = model.predict_step(current_state, inputs, dt=0.1)

        assert isinstance(result, dict)
        assert 'cod' in result
        assert 'flowrate' in result
        assert 'model_type' in result
        assert result['model_type'] == 'Linear'

    def test_initialize_state(self):
        """Test : initialisation de l'état"""
        model = LinearModel()

        initial = {'cod': 200.0, 'tss': 2500.0}
        state = model.initialize_state(initial)

        assert isinstance(state, dict)
        assert state['cod'] == 200.0
        assert state['tss'] == 2500.0

    def test_save_load(self, sample_training_data, tmp_path):
        """Test : save et load"""
        X, y = sample_training_data
        model = LinearModel()
        model.fit(X, y)

        model_path = tmp_path / "linear_model.pkl"
        model.save(str(model_path))

        assert model_path.exists()

        loaded_model = LinearModel()
        loaded_model.load(str(model_path))

        assert loaded_model.is_fitted is True
        assert len(loaded_model.feature_names) == len(model.feature_names)

    @pytest.mark.parametrize('param_name,param_value', [
        ('custom_param', 42)
    ])
    def test_custom_parameters(self, param_name, param_value):
        """Test : paramètres personnalisés"""
        model = LinearModel(params={param_name: param_value})

        assert model.params[param_name] == param_value

class TestRandomForest:
    """Tests pour RandomForest"""

    def test_initialization(self):
        """Test : initialisation"""
        model = RandomForestModel()

        assert model is not None
        assert hasattr(model, 'model')
        assert hasattr(model, 'scaler')

    def test_initialization_with_params(self):
        """Test : initialisation avec paramètres"""
        params = {
            'n_estimators': 50,
            'max_depth': 5
        }
        model = RandomForestModel(params=params)

        rf_params = model.model.get_params()

        assert rf_params['n_etimators'] == 50
        assert rf_params['max_depth'] == 5

    def test_model_type(self):
        """Test : model_type"""
        model = RandomForestModel()

        assert model.model_type == "RandomForest"

    def test_fit(self, sample_training_data):
        """Test : entraînement"""
        X, y = sample_training_data
        model = RandomForestModel()

        result = model.fit(X, y)

        assert 'r2_score' in result
        assert 'feature_importances' in result
        assert model.is_fitted is True

    def test_predict_step_after_training(self, sample_training_data):
        """Test : prédiction après entraînement"""
        X, y = sample_training_data
        model = RandomForestModel()
        model.fit(X, y)

        current_state = {
            'cod': 100.0,
            'tss': 2000.0
        }
        inputs = {
            'flowrate': 1000.0,
            'temperature': 20.0
        }

        result = model.predict_step(current_state, inputs, dt=0.1)

        assert isinstance(result, dict)
        assert 'cod' in result
        assert 'model_type' in result
        assert result['model_type'] == 'RandomForest'

    def test_save_load(self, sample_training_data, tmp_path):
        """Test : save et load"""
        X, y = sample_training_data
        model = RandomForestModel()
        model.fit(X, y)

        model_path = tmp_path / "rf_model.pkl"
        model.save(str(model_path))

        assert model_path.exists()

        loaded_model = RandomForestModel()
        loaded_model.load(str(model_path))

        assert loaded_model.is_fitted is True

class TestMLModelEdgeCases:
    """Tests de cas limites pour les modèles ML"""
    
    def test_empy_state(self):
        """Test : état vide"""
        model = LinearModel()

        state = model.initialize_state({})

        assert isinstance(state, dict)

    def test_predict_with_missing_features(self, sample_training_data):
        """Test : prédiction avec features manquantes"""
        X, y = sample_training_data
        model = LinearModel()
        model.fit(X, y)

        state = {'cod': 100.0}
        inputs = {'flowrate': 1000.0}

        result = model.predict_step(state, inputs, dt=0.1)
        
        assert result is not None

    def test_very_small_dataset(self):
        """Test : dataset très petit"""
        X = np.random.randn(5, 10)
        y = np.random.randn(5, 7)

        model = LinearModel()

        result = model.fit(X, y)

        assert 'r2_score' in result