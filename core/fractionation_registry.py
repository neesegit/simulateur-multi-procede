"""
Registre centralisé pour le fractionnement des modèles
"""
from typing import Dict, Any, Optional, Callable
from abc import ABC, abstractmethod
import logging

logger = logging.getLogger(__name__)

class FractionationStrategy(ABC):
    """Interface pour les stratégies de fractionnement"""

    @abstractmethod
    def fractionate(self, **kwargs) -> Dict[str, float]:
        """Fractionne les paramètres mesurés en composants du modèle"""
        pass

    @abstractmethod
    def get_required_inputs(self) -> list[str]:
        """Retourne la liste des inputs requis pour le fractionnement"""
        pass

class NoFractionationStrategy(FractionationStrategy):
    """Stratégie pour les modèles qui ne nécessitent pas de fractionnement"""

    def fractionate(self, **kwargs) -> Dict[str, float]:
        """Retourne les composants tels quels"""
        components = kwargs.get('components', {})
        return components
    
    def get_required_inputs(self) -> list[str]:
        return []
    
class FractionationRegistry:
    """Registre centralisé des stratégies de fractionnement"""

    _instance = None
    
    def __init__(self):
        self._strategies: Dict[str, FractionationStrategy] = {}
        self._register_default_strategies()

    @classmethod
    def get_instance(cls) -> 'FractionationRegistry':
        """Retourne l'instance singleton"""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance
    
    def _register_default_strategies(self):
        """Enregistre les stratégies par défaut"""
        try:
            from models.empyrical.asm1.fraction import ASM1Fraction
            self.register('ASM1', ASM1FractionationStrategy(ASM1Fraction))
            self.register('ASM1Model', ASM1FractionationStrategy(ASM1Fraction))
        except ImportError:
            logger.warning("ASM1Fraction non disponible")

        try:
            from models.empyrical.asm2d.fraction import ASM2DFraction
            self.register('ASM2D', ASM2DFractionationStrategy(ASM2DFraction))
            self.register('ASM2dModel', ASM2DFractionationStrategy(ASM2DFraction))
        except ImportError:
            logger.warning("ASM2DFraction non disponible")

        try:
            from models.empyrical.asm3.fraction import ASM3Fraction
            self.register('ASM3', ASM3FractionationStrategy(ASM3Fraction))
            self.register('ASM3Model', ASM3FractionationStrategy(ASM3Fraction))
        except ImportError:
            logger.warning("ASM3Fraction non disponible")

        self.register('LinearModel', NoFractionationStrategy())
        self.register('RandomForestModel', NoFractionationStrategy())
        
        self.register('TakacsModel', NoFractionationStrategy())

    def register(self, model_type: str, strategy: FractionationStrategy):
        """Enregistre une stratégie pour un type de modèle"""
        self._strategies[model_type.upper()] = strategy
        logger.debug(f"Stratégie de fractionnement enregistrée pour {model_type}")
    
    def get_strategy(self, model_type: str) -> FractionationStrategy:
        """récupère la stratégie pour un type de modèle"""
        strategy = self._strategies.get(model_type.upper())

        if strategy is None:
            logger.warning(
                f"Aucune stratégie de fractionnement pour {model_type}"
                "Utilisation de NoFractionationStrategy."
            )
            return NoFractionationStrategy()
        
        return strategy
    
    def fractionate(
            self,
            model_type: str,
            cod: float = 0,
            tss: float = 0,
            tkn: float = 0,
            nh4: float = 0,
            no3: float = 0,
            po4: float = 0,
            alkalinity: Optional[float] = None,
            **kwargs
    ) -> Dict[str, float]:
        """
        Fractionne les paramètres selon le modèle

        Args:
            model_type (str): Type de modèle
            cod (float, optional): DCO totale. Defaults to 0.
            tss (float, optional): Solides en suspension. Defaults to 0.
            tkn (float, optional): Azote Kjeldahl total. Defaults to 0.
            nh4 (float, optional): Ammonium. Defaults to 0.
            no3 (float, optional): Nitrates. Defaults to 0.
            po4 (float, optional): Phosphates. Defaults to 0.
            alkalinity (Optional[float], optional): Alcalinité. Defaults to None.
            **kwargs: Autres paramètres spécifiques au modèle

        Returns:
            Dict[str, float]: Dict des composants fractionnés
        """
        strategy = self.get_strategy(model_type)

        return strategy.fractionate(
            cod=cod,
            tss=tss,
            nh4=nh4,
            no3=no3,
            po4=po4,
            alkalinity=alkalinity,
            **kwargs
        )
    
class ASM1FractionationStrategy(FractionationStrategy):
    """Stratégie de fractionneemnt pour ASM1"""

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
            cod_soluble=kwargs.get('cod_soluble')
        )
    
    def get_required_inputs(self) -> list[str]:
        return ['cod', 'tss', 'tkn', 'nh4', 'no3', 'po4']
    
class ASM2DFractionationStrategy(FractionationStrategy):
    """Stratégie de fractionnement pour ASM2D"""

    def __init__(self, fraction_class):
        self.fraction_class = fraction_class

    def fractionate(self, **kwargs) -> Dict[str, float]:
        return self.fraction_class.fractionate(
            cod=kwargs.get('cod', 0),
            tss=kwargs.get('tss', 0),
            tkn=kwargs.get('tkn', 0),
            nh4=kwargs.get('nh4', 0),
            no3=kwargs.get('no3', 0),
            tp=kwargs.get('tp', 0),
            po4=kwargs.get('po4', 0),
            alkalinity=kwargs.get('alkalinity'),
            cod_soluble=kwargs.get('cod_soluble'),
            rbcod=kwargs.get('rbcod'),
            vfa=kwargs.get('vfa')
        )
    
    def get_required_inputs(self) -> list[str]:
        return ['cod', 'tss', 'tkn', 'nh4', 'no3', 'tp', 'po4']
    
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