"""
Registre centralisé pour le calcul des métriques de performance
"""
from typing import Dict, Any, Callable, Optional
from abc import ABC, abstractmethod
import numpy as np
import logging

logger = logging.getLogger(__name__)

class MetricCalculator(ABC):
    """Interface pour les calculateurs de métriques"""

    @abstractmethod
    def calculate(
        self,
        components: Dict[str, float],
        inputs: Dict[str, Any],
        context: Dict[str, Any]
    ) -> Dict[str, float]:
        """Calcule les métriques"""
        pass

class CompositeMetricCalculator(MetricCalculator):
    """Calculateur qui combine plusieurs composants"""

    def __init__(self, component_names: list[str]):
        self.component_names = component_names

    def calculate(self, components: Dict[str, float], inputs: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, float]:
        return {
            'value': sum(components.get(name, 0.0) for name in self.component_names)
        }
    
class RemovalEfficiencyCalculator(MetricCalculator):
    """Calcule l'efficacité d'élimination"""

    def __init__(self, input_key: str, output_key: str):
        self.input_key = input_key
        self.output_key = output_key

    def calculate(self, components: Dict[str, float], inputs: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, float]:
        value_in = inputs.get(self.input_key, 0)
        value_out = components.get(self.output_key, 0)

        if value_in > 0:
            efficiency = max(0, (value_in - value_out) / value_in * 100)
            return {'efficiency': min(98.0, efficiency)}
        return {'efficiency': 0.0}
    
class EnergyConsumptionCalculator(MetricCalculator):
    """Calcule la consommation énergétique"""

    def calculate(self, components: Dict[str, float], inputs: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, float]:
        cod_in = inputs.get('cod_in', 0)
        cod_out = components.get('cod', 0)
        flowrate = inputs.get('flowrate', 0)
        dt = context.get('dt', 0)

        cod_removed_mg = max(0, cod_in - cod_out)
        oxygen_consumed_kg = (cod_removed_mg * flowrate * dt) / 1000.0
        aeration_energy_kwh = max(0, oxygen_consumed_kg * 2.0)

        total_volume_m3 = flowrate * dt
        energy_per_m3 = aeration_energy_kwh / total_volume_m3 if total_volume_m3 > 0 else 0

        return {
            'oxygen_consumed_kg': oxygen_consumed_kg,
            'aeration_energy_kwh': aeration_energy_kwh,
            'energy_per_m3': energy_per_m3
        }
    
class HRTCalculator(MetricCalculator):
    """Calcule le temps de rétention hydraulique"""

    def calculate(self, components: Dict[str, float], inputs: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, float]:
        volume = context.get('volume', 0)
        flowrate = inputs.get('flowrate', 0)

        hrt_hours = volume / flowrate if flowrate > 0 else 0
        hrt_hours = np.clip(hrt_hours, 2.0, 48.0)

        return {'hrt_hours': hrt_hours}
    
class SRTCalculator(MetricCalculator):
    """Calcule le temps de rétention des solides"""

    def calculate(self, components: Dict[str, float], inputs: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, float]:
        mlss = components.get('tss', 0)
        volume = context.get('volume', 0)
        flowrate = inputs.get('flowrate', 0)
        waste_ratio = context.get('waste_ratio', 0.01)

        if flowrate > 0 and mlss > 100:
            waste_flow = flowrate * waste_ratio
            total_solids_kg = mlss * volume / 1000.0
            wasted_solids_kg_per_day = waste_flow * mlss * 24 / 1000.0

            srt_days = total_solids_kg / wasted_solids_kg_per_day
            srt_days = np.clip(srt_days, 3.0, 50.0)
        else:
            srt_days = 20.0

        return {'srt_days': srt_days}
    
class SVICalculator(MetricCalculator):
    """Calcule l'indice de volume des boues"""

    def calculate(self, components: Dict[str, float], inputs: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, float]:
        mlss = components.get('tss', 0)
        volume = context.get('volume', 0)

        if mlss > 100:
            settled_volume = volume * 0.30
            settled_volume_L = settled_volume * 1000
            mlss_g_L = mlss / 1000.0

            svi = (settled_volume_L / (mlss_g_L * volume)) * 1000
            svi = np.clip(svi, 80.0, 200.0)
        else:
            svi = 120.0

        return {'svi': svi}
    
class MetricsRegistry:
    """Registre centralisé des métriques de performance"""

    _instance = None

    def __init__(self):
        self._calculators: Dict[str, MetricCalculator] = {}
        self._model_metrics: Dict[str, list[str]] = {}
        self._register_default_calculators()

    @classmethod
    def get_instance(cls) -> 'MetricsRegistry':
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance
    
    def _register_default_calculators(self):
        """Enregistre les calculateurs par défaut"""

        self.register('hrt', HRTCalculator())
        self.register('srt', SRTCalculator())
        self.register('svi', SVICalculator())
        self.register('energy', EnergyConsumptionCalculator())

        self._model_metrics['ASM1Model'] = ['cod', 'tkn', 'tss', 'biomass', 'hrt', 'srt', 'svi', 'energy']
        self._model_metrics['ASM2dModel'] = ['cod', 'tkn', 'tss', 'biomass', 'hrt', 'srt', 'svi', 'energy']
        self._model_metrics['ASM3Model'] = ['cod', 'tkn', 'tss', 'biomass', 'hrt', 'srt', 'svi', 'energy']
        self._model_metrics['TakacsModel'] = ['removal_efficiency', 'surface_loading', 'solids_loading']

    def register(self, metric_name: str, calculator: MetricCalculator):
        """Enregistre un calculateur de métrique"""
        self._calculators[metric_name] = calculator
        logger.debug(f"Calculateur de métrique enregistré : {metric_name}")

    def register_model_metrics(self, model_type: str, metric_names: list[str]):
        """Associe des métriques à un type de modèle"""
        self._model_metrics[model_type] = metric_names

    def get_model_metrics(self, model_type: str) -> list[str]:
        """Retourne les métriques applicables à un modèle"""
        return self._model_metrics.get(model_type, [])
    
    def calculate(
            self,
            metric_name: str,
            components: Dict[str, float],
            inputs: Dict[str, Any],
            context: Dict[str, Any]
    ) -> Dict[str, float]:
        """Calcule une métrique spécifique"""
        calculator = self._calculators.get(metric_name)

        if calculator is None:
            logger.warning(f"Aucun calculateur pour la métrique : {metric_name}")
            return {}
        
        try:
            return calculator.calculate(components, inputs, context)
        except Exception as e:
            logger.error(f"Erreur lors du calcul de {metric_name} : {e}")
            return {}
        
    def calculate_all_for_model(
            self,
            model_type: str,
            components: Dict[str, float],
            inputs: Dict[str, Any],
            context: Dict[str, Any]
    ) -> Dict[str, float]:
        """Calcule toutes les métriques pour un modèle"""
        results = {}

        metric_names = self.get_model_metrics(model_type)

        for metric_name in metric_names:
            metric_results = self.calculate(metric_name, components, inputs, context)
            results.update(metric_results)

        return results
    
def create_composite_calculator(
        model_definition: Any,
        metric_type: str
) -> Optional[MetricCalculator]:
    """
    Crée un calculateur composite basé sur la définition du modèle

    Args:
        model_definition (Any): Définition du modèle depuis le registre
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