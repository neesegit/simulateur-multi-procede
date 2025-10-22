from typing import Dict, Any
from datetime import datetime
from core.data.flow_data import FlowData

class InfluentInitializer:
    @staticmethod
    def create_from_config(config: Dict[str, Any], current_time: datetime) -> 'FlowData':
        """
        Crée le FlowData initial de l'influent à partir de la config
        """
        influent_config = config.get('influent', {})
        return FlowData.create_from_model(
            timestamp=current_time,
            flowrate=influent_config.get('flowrate', 1000.0),
            temperature=influent_config.get('temperature', 20.0),
            model_type=influent_config.get('model_type', 'ASM1'),
            auto_fractionate=influent_config.get('auto_fractionate', True),
            **influent_config.get('composition', {})
        )