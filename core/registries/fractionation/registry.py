"""Registre centralisé pour le fractionnement des modèles"""
import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional

from .strategies import (
    FractionationStrategy,
    NoFractionationStrategy,
    ASM1FractionationStrategy,
    ASM2DFractionationStrategy,
    ASM3FractionationStrategy,
)

logger = logging.getLogger(__name__)

_CONFIG_DIR = Path(__file__).parent / 'config'


def _build_asm1() -> Optional[FractionationStrategy]:
    try:
        from models.empyrical.asm1.fraction import ASM1Fraction
        return ASM1FractionationStrategy(ASM1Fraction)
    except ImportError:
        logger.warning("ASM1Fraction non disponible")
        return None


def _build_asm2d() -> Optional[FractionationStrategy]:
    try:
        from models.empyrical.asm2d.fraction import ASM2DFraction
        return ASM2DFractionationStrategy(ASM2DFraction)
    except ImportError:
        logger.warning("ASM2DFraction non disponible")
        return None


def _build_asm3() -> Optional[FractionationStrategy]:
    try:
        from models.empyrical.asm3.fraction import ASM3Fraction
        return ASM3FractionationStrategy(ASM3Fraction)
    except ImportError:
        logger.warning("ASM3Fraction non disponible")
        return None


_STRATEGY_CONSTRUCTORS = {
    'NoFractionationStrategy': lambda: NoFractionationStrategy(),
    'ASM1FractionationStrategy': _build_asm1,
    'ASM2DFractionationStrategy': _build_asm2d,
    'ASM3FractionationStrategy': _build_asm3,
}


class FractionationRegistry:
    """Registre centralisé des stratégies de fractionnement"""

    _instance = None

    def __init__(self):
        self._strategies: Dict[str, FractionationStrategy] = {}
        self._default_models: set = set()
        self._register_defaults()

    @classmethod
    def get_instance(cls) -> 'FractionationRegistry':
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def _register_defaults(self):
        """Charge les associations modèle → stratégie depuis model_strategies.json"""
        config_path = _CONFIG_DIR / 'model_strategies.json'
        if not config_path.exists():
            logger.warning(f"model_strategies.json introuvable : {config_path}")
            return

        with open(config_path, encoding='utf-8') as f:
            model_strategies: Dict[str, str] = json.load(f)

        for model_key, strategy_name in model_strategies.items():
            builder = _STRATEGY_CONSTRUCTORS.get(strategy_name)
            if builder is None:
                logger.warning(f"Constructeur inconnu pour '{strategy_name}' (modèle {model_key})")
                continue
            strategy = builder()
            if strategy is None:
                continue
            try:
                self.register(model_key, strategy, default=True)
            except ValueError:
                pass  # alias déjà enregistré via un nom différent

    def register(self, model_type: str, strategy: FractionationStrategy, default: bool = False):
        """Enregistre une stratégie pour un type de modèle"""
        key = model_type.upper()
        if key in self._strategies:
            raise ValueError(f"Model type '{key}' is already registered")
        self._strategies[key] = strategy
        if default:
            self._default_models.add(key)
        logger.debug(f"Stratégie de fractionnement enregistrée pour {model_type}")

    def get_strategy(self, model_type: str) -> FractionationStrategy:
        """Récupère la stratégie pour un type de modèle"""
        key = model_type.upper()
        if key not in self._strategies:
            raise ValueError(
                f"Model type '{key}' is not registered. "
                f"Available models: {list(self._strategies.keys())}"
            )
        return self._strategies[key]

    def list_registered_models(self) -> list[str]:
        return sorted(self._strategies.keys())

    def is_registered(self, model_type: str) -> bool:
        return model_type.upper() in self._strategies

    def unregister(self, model_type: str) -> None:
        key = model_type.upper()
        if key in self._default_models:
            raise ValueError(f"Cannot unregister default model '{key}'")
        if key not in self._strategies:
            raise ValueError(f"Model type '{key}' is not registered")
        del self._strategies[key]
        logger.debug(f"Stratégie de fractionnement supprimée pour {key}")

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
    ) -> Dict[str, Any]:
        """Fractionne les paramètres selon le modèle"""
        strategy = self.get_strategy(model_type)
        return strategy.fractionate(
            cod=cod, tss=tss, tkn=tkn, nh4=nh4,
            no3=no3, po4=po4, alkalinity=alkalinity,
            **kwargs
        )
