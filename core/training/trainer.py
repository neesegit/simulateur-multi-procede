import logging
import numpy as np
import pandas as pd

from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Any, Tuple

from core.training.training_cache import MLTrainingCache
from core.training.configuration_comparator import MLConfigurationComparator
from core.model.model_registry import ModelRegistry

from utils.input_helpers import ask_yes_no

logger = logging.getLogger(__name__)

class MLTrainer:
    """
    Gère l'entraînement des modèles ML pour un procédé
    Similaire au calibration pour les modèles empyriques
    """

    def __init__(
            self,
            process_id: str,
            process_config: Dict[str, Any],
            model_type: str,
            training_data_path: Optional[Path] = None
    ):
        self.process_id = process_id
        self.process_config = process_config
        self.model_type = model_type
        self.training_data_path = training_data_path

        self.cache = MLTrainingCache()
        self.comparator = MLConfigurationComparator()

        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")

        self.logger.info(f"MLTrainer initialisé pour {model_type} ({process_id})")

    def check_training_needed(self) -> Tuple[bool, Optional[str]]:
        """Vérifie si un entraînement est nécessaire"""
        current_hash = self.comparator.compute_hash(self.process_config)

        if not self.cache.exists(self.process_id, self.model_type, current_hash):
            return True, "Aucun modèle entraîné en cache"
        
        metadata = self.cache.load_metadata(self.process_id, self.model_type, current_hash)
        if metadata is None:
            return True, "Erreur lors de la lecture des métadonnées"
        
        if current_hash != metadata.get('config_hash'):
            config_diff = self.comparator.compare_configs(
                self.process_config,
                metadata.get('process_config', {})
            )

            reason = (
                f"configuration modifiée depuis l'entraînement "
                f"({metadata.get('trained_at', 'date inconnue')})\n"
            )

            if config_diff['modified']:
                reason += f"\tParamètre modifiés : {list(config_diff['modified'].keys())}\n"
            if config_diff['added']:
                reason += f"\tParamètres ajoutés : {list(config_diff['added'].keys())}\n"
            if config_diff['removed']:
                reason += f"\tParamètres supprimés : {list(config_diff['removed'].keys())}"

            return True, reason
        return False, None
    
    def train(
            self,
            skip_if_exists: bool = False,
            interactive: bool = False
    ) -> Optional[Path]:
        """
        Lance l'entraînement du modèle ML

        Args:
            skip_if_exists (bool, optional): Utilise le modèle existant si disponible. Defaults to False.
            interactive (bool, optional): Demande confirmation à l'utilisateur. Defaults to False.

        Returns:
            Optional[Path]: Path vers le modèle entraîné ou None
        """
        print("\n"+"="*70)
        print(f"Entraînement ML - {self.model_type} ({self.process_id})")
        print("="*70)

        needed, reason = self.check_training_needed()
        current_hash = self.comparator.compute_hash(self.process_config)

        if not needed:
            print(f"\nModèle ML valide et à jour")
            metadata = self.cache.load_metadata(self.process_id, self.model_type, current_hash)
            if metadata:
                print(
                    f"\tEntraîné le : {metadata.get('trained_at')}\n"
                    f"\tScore R² : {metadata.get('r2_score', 'N/A')}\n"
                    f"\tEchantillons : {metadata.get('n_samples', 'N/A')}\n"
                    f"\tHash config : {current_hash[:8]}"
                )
            model_path = self.cache.get_cache_path(self.process_id, self.model_type, current_hash)
            return model_path
        
        print(f"\nEntraînement nécessaire : {reason}")

        if skip_if_exists:
            print("-> Utilisation du dernier modèle entraîné")
            model_path = self.cache.get_cache_path(self.process_id, self.model_type, current_hash)
            if model_path.exists():
                return model_path
            else:
                print("-> Aucun modèle trouvé, entraînement requis")
        
        if interactive:
            response = ask_yes_no("Lancer l'entraînement du modèle ML ?")
            if response:
                model_path = self.cache.get_cache_path(self.process_id, self.model_type, current_hash)
                return model_path if model_path.exists() else None

        return self._run_training()
    
    def _run_training(self) -> Optional[Path]:
        """Exécute l'entraînement du modèle"""
        start_time = datetime.now()

        try:
            registry = ModelRegistry.get_instance()
            model_params = self.process_config.get('config', {}).get('model_parameters', {})
            model_instance = registry.create_model(
                model_type=self.model_type,
                params=model_params
            )

            print("\n"+"-"*70)
            print("Chargement des données d'entraînement ...")
            print("-"*70)

            try:
                assert self.training_data_path is not None
                X_train, y_train = self._load_training_data(self.training_data_path)
            except Exception as e:
                print(f"Problème lors du chargement des données d'entrainement : {e}")
                raise

            print(f"Données chargées : {X_train.shape[0]} échantillons, {X_train.shape[1]} features")

            print("\n"+"-"*70)
            print("Entrainement en cours ...")
            print("-"*70)

            training_results = model_instance.fit(X_train, y_train)

            current_hash = self.comparator.compute_hash(self.process_config)
            model_path = self.cache.get_cache_path(self.process_id, self.model_type, current_hash)

            model_instance.save(str(model_path))

            elapsed = (datetime.now() - start_time).total_seconds()
            metadata = {
                'process_id': self.process_id,
                'model_type': self.model_type,
                'config_hash': current_hash,
                'trained_at': datetime.now().isoformat(),
                'training_duration_seconds': elapsed,
                'n_samples': X_train.shape[0],
                'n_features': X_train.shape[1],
                'r2_score': training_results.get('r2_score', 0),
                'process_config': self.process_config
            }
            
            self.cache.save_metadata(self.process_id, self.model_type, current_hash, metadata)

            print("\n"+"="*70)
            print("Entrainement terminé avec succès")
            print("="*70)
            print(f"Modèle sauvegardé : {model_path}")
            print(f"Score R² : {training_results.get('r2_score', 'N/A'):.4f}")
            print(f"Durée : {elapsed:.1f}s")
            print("="*70+"\n")

            return model_path
        
        except Exception as e:
            self.logger.error(f"Erreur lors de l'entraînement : {e}", exc_info=True)
            print(f"\nErreur : {e}")
            return None
        
    def _load_training_data(self, data_path: Path) -> Tuple[Any, Any]:
        """Charge les données d'entraînement depuis un fichier"""

        if data_path.suffix != '.csv':
            raise ValueError(f"Format de fichier non supporté : {data_path.suffix}")
        
        df = pd.read_csv(data_path)

        if df.columns[0] == 'Unnamed: 0' or df.columns[0].isdigit():
            df = df.iloc[:, 1:]
        
        self.logger.info(f"Données chargées : {len(df)} lignes, {len(df.columns)} colonnes")

        feature_cols = [
            'Average Inflow', #flowrate
            'Average Temperature', #temperature
            'Ammonia', #nh4_in
            'Biological Oxygen Demand', #bod_in
            'Chemical Oxygen Demand', #cod_in
            'Total Nitrogen', #tkn_in
            'Average humidity' # conditions météo
            'Total rainfall',
            'Average wind speed'
        ]

        target_cols = [
            'Average Outflow', #flowrate_out
            'Energy Consumption', #energie consommée
        ]

        missing_features = [col for col in feature_cols if col not in df.columns]
        if missing_features:
            self.logger.warning(f"Collonnes features manquantes : {missing_features}")
            feature_cols = [col for col in feature_cols if col in df.columns]

        missing_targets = [col for col in target_cols if col not in df.columns]
        if missing_targets:
            self.logger.warning(f"Collones targets manquantes : {missing_targets}")
            target_cols = [col for col in target_cols if col in df.columns]

        X = df[feature_cols].copy()

        volume = self.process_config.get('config', {}).get('volume', 5000.0)
        X['volume'] = volume

        X['hrt_hours'] = volume / (df['Average Inflow'] + 0.001)

        X['srt_days'] = 20.0

        y = df[target_cols].copy()

        cod_removal_rate = 0.90
        y['cod'] = df['Chemical Oxygen Demand'] * (1 - cod_removal_rate)

        y['ss'] = 2000 + np.random.normal(0, 200, len(df))

        y['nh4'] = df['Ammonia'] * 0.1

        y['no3'] = df['Total Nitrogen'] * 0.6

        y['po4'] = 1.0

        y['biomass'] = y['ss'] * 0.75

        y['cod_removal'] = cod_removal_rate * 100

        X = X.replace([np.inf, -np.inf], np.nan)
        y = y.replace([np.inf, -np.inf], np.nan)

        X = X.fillna(X.mean())
        y = y.fillna(y.mean())

        self.logger.info(f"Features finales : {list(X.columns)}")
        self.logger.info(f"Targets finales : {list(y.columns)}")
        self.logger.info(f"Shape - X : {X.shape}, y : {y.shape}")

        return X.values, y.values