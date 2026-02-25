"""Stratégie de fractionnement pour ASM3"""
from typing import Dict
from .base import FractionationStrategy


class ASM3FractionationStrategy(FractionationStrategy):
    """Stratégie de fractionnement pour ASM3"""

    def __init__(self, fraction_class):
        self.fraction_class = fraction_class

    def fractionate(self, **kwargs) -> Dict[str, float]:
        return self.fraction_class.fractionate(
            cod=kwargs.get('cod', 0),
            tss=kwargs.get('tss', 0),
            tkn=kwargs.get('tkn', 0),
            nh4=kwargs.get('nh4', 0),
            no3=kwargs.get('no3', 0),
            po4=kwargs.get('po4', 0),
            alkalinity=kwargs.get('alkalinity'),
            cod_soluble=kwargs.get('cod_soluble'),
            rbcod=kwargs.get('rbcod')
        )

    def get_required_inputs(self) -> list[str]:
        return ['cod', 'tss', 'tkn', 'nh4', 'no3', 'po4']
