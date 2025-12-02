import logging

from pathlib import Path
from typing import Dict, Any, Optional, List

from core.training.trainer import MLTrainer
from core.model.model_registry import ModelRegistry

class MLTrainingManager:
    """
    Orchestre l'entraînement des modèles ML pour une simulation complète
    Equivalent du CalibrationManager pour les modèles empyrique
    """

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.trainers: Dict[str, MLTrainer] = {}

        self.registry = ModelRegistry.get_instance()

    def create_trainers(self) -> List[MLTrainer]:
        """Crée les trainers pour tous les processus ML"""
        self.trainers.clear()
        trainers = []

        processes_config = self.config.get('processes', [])

        for proc_config in processes_config:
            process_id = proc_config.get('node_id')
            model_type = proc_config.get('config', {}).get('model')

            if not self._is_ml_model(model_type):
                continue

            training_data_path = proc_config.get('config', {}).get('training_data_path')
            if training_data_path:
                training_data_path = Path(training_data_path)

            trainer = MLTrainer(
                process_id=process_id,
                process_config=proc_config,
                model_type=model_type,
                training_data_path=training_data_path
            )

            self.trainers[process_id] = trainer
            trainers.append(trainer)

        return trainers
    
    def _is_ml_model(self, model_type: str) -> bool:
        """Vérifie si le modèle est de type ML"""
        ml_models = self.registry.get_ml_models()
        return model_type in ml_models
    
    def train_all(
            self,
            skip_if_exists: bool = False,
            interactive: bool = False
    ) -> Dict[str, Optional[Path]]:
        """
        Lance l'entraînement pour tous les modèles ML

        Returns:
            Dict[str, Optional[Path]]: Dict[process_id, model_path]
        """
        trainers = self.create_trainers()
        results = {}

        if not trainers:
            self.logger.info("Aucun modèle ML à entraîner")
            return results
        
        print("\n"+"="*70)
        print(f"Gestion de l'entrainement ML - {len(trainers)} modèle(s)")
        print("="*70)

        for trainer in trainers:
            model_path = trainer.train(
                skip_if_exists=skip_if_exists,
                interactive=interactive
            )
            results[trainer.process_id] = model_path
        return results