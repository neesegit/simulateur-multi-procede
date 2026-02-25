"""Registre centralisé pour le calcul des métriques de performance"""
import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional

from .calculators import (
    MetricCalculator, CompositeMetricCalculator,
    HRTCalculator, SRTCalculator, SVICalculator, EnergyConsumptionCalculator
)

logger = logging.getLogger(__name__)

_CONFIG_DIR = Path(__file__).parent / 'config'


class MetricsRegistry:
    """Registre centralisé des métriques de performance"""

    _instance = None

    def __init__(self):
        self._calculators: Dict[str, MetricCalculator] = {}
        self._model_metrics: Dict[str, list[str]] = {}
        self._default_metrics: set = set()
        self._register_defaults()

    @classmethod
    def get_instance(cls) -> 'MetricsRegistry':
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def _register_defaults(self):
        """Charge les calculateurs et associations depuis les JSON de config"""
        # Paramètres des calculateurs
        calc_config: Dict[str, Any] = {}
        calc_path = _CONFIG_DIR / 'calculators.json'
        if calc_path.exists():
            with open(calc_path, encoding='utf-8') as f:
                calc_config = json.load(f)
        else:
            logger.warning(f"calculators.json introuvable : {calc_path}")

        self.register('hrt', HRTCalculator(**calc_config.get('hrt', {})), default=True)
        self.register('srt', SRTCalculator(**calc_config.get('srt', {})), default=True)
        self.register('svi', SVICalculator(**calc_config.get('svi', {})), default=True)
        self.register('energy', EnergyConsumptionCalculator(), default=True)

        # Associations modèle → métriques
        metrics_path = _CONFIG_DIR / 'model_metrics.json'
        if metrics_path.exists():
            with open(metrics_path, encoding='utf-8') as f:
                model_metrics: Dict[str, list] = json.load(f)
            for model_type, metrics in model_metrics.items():
                self._model_metrics[model_type] = metrics
        else:
            logger.warning(f"model_metrics.json introuvable : {metrics_path}")

    def register(self, metric_name: str, calculator: MetricCalculator, default: bool = False):
        """Enregistre un calculateur de métrique"""
        metric_name = metric_name.lower()
        if metric_name in self._calculators:
            raise ValueError(f"Calculator type {metric_name} is already registered")
        self._calculators[metric_name] = calculator
        if default:
            self._default_metrics.add(metric_name)
        logger.debug(f"Calculateur de métrique enregistré : {metric_name}")

    def register_model_metrics(self, model_type: str, metric_names: list[str]):
        """Associe des métriques à un type de modèle"""
        self._model_metrics[model_type] = metric_names

    def get_model_metrics(self, model_type: str) -> list[str]:
        """Retourne les métriques applicables à un modèle"""
        return self._model_metrics.get(model_type, [])

    def get_calculator(self, metric_name: str) -> MetricCalculator:
        """Récupère le calculateur pour un type de métrique"""
        if metric_name not in self._calculators:
            raise ValueError(
                f"Calculator type '{metric_name}' is not registered. "
                f"Available calculators: {list(self._calculators.keys())}"
            )
        return self._calculators[metric_name]

    def list_registered_metrics(self) -> list[str]:
        return sorted(self._calculators.keys())

    def is_registered(self, metric_name: str) -> bool:
        return metric_name in self._calculators

    def unregister(self, metric_name: str) -> None:
        if metric_name in self._default_metrics:
            raise ValueError(f"Cannot unregister default calculator '{metric_name}'")
        if metric_name not in self._calculators:
            raise ValueError(f"Calculator type '{metric_name}' is not registered")
        del self._calculators[metric_name]
        logger.debug(f"Calculateur de métrique supprimé : {metric_name}")

    def calculate(
        self,
        metric_name: str,
        components: Dict[str, float],
        inputs: Dict[str, Any],
        context: Dict[str, Any]
    ) -> Dict[str, float]:
        """Calcule une métrique spécifique"""
        calculator = self.get_calculator(metric_name)
        try:
            return calculator.calculate(components, inputs, context)
        except ValueError as e:
            raise ValueError(f"Erreur lors du calcul de {metric_name} : {e}")

    def calculate_all_for_model(
        self,
        model_type: str,
        components: Dict[str, float],
        inputs: Dict[str, Any],
        context: Dict[str, Any]
    ) -> Dict[str, float]:
        """Calcule toutes les métriques pour un modèle"""
        results = {}
        for metric_name in self.get_model_metrics(model_type):
            results.update(self.calculate(metric_name, components, inputs, context))
        return results


def create_composite_calculator(
    model_definition: Any,
    metric_type: str
) -> Optional[MetricCalculator]:
    """
    Crée un calculateur composite basé sur la définition du modèle

    Args:
        model_definition: Définition du modèle depuis le registre
        metric_type (str): Type de métrique ('cod', 'tkn', 'tss', 'biomass')

    Returns:
        Optional[MetricCalculator]: composite ou None
    """
    metrics_dict = model_definition.get_metrics_dict()
    component_names = metrics_dict.get(metric_type)

    if component_names is None:
        return None

    if isinstance(component_names, str):
        component_names = [component_names]

    return CompositeMetricCalculator(component_names)
