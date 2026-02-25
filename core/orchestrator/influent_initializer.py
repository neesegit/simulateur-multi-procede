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
        composition = influent_config.get('composition', {})

        flow = FlowData(
            timestamp=current_time,
            flowrate=influent_config.get('flowrate', 1000.0),
            temperature=influent_config.get('temperature', 20.0),
            source_node='influent'
        )

        for attr in ('cod', 'tkn', 'bod', 'nh4', 'no3', 'po4', 'alkalinity'):
            setattr(flow, attr, composition.get(attr, 0.0))
        flow.tss = composition.get('tss', composition.get('ss', 0.0))
        return flow