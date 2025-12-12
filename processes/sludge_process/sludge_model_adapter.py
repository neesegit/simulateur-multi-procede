"""
Module qui permet d'adapter les différents modèles à une interface commune
"""
import numpy as np
import logging

from typing import Dict, Any, Optional
from core.calibration.calibration_cache import CalibrationCache
from core.calibration.configuration_comparator import ConfigurationComparator

logger = logging.getLogger(__name__)

class SludgeModelAdapter:
    """
    Adaptateur pour fournir une interface uniforme aux modèles biologiques
    """

    def __init__(self, model_instance: Any, model_name: str) -> None:
        self.name = model_name.upper()
        self.model = model_instance

        self.size = len(self.model.COMPONENT_INDICES)
        logger.debug(f"Adaptateur initialisé pour {self.name} ({self.size} composants)")

    def dict_to_vector(self, data: Dict[str, float]) -> np.ndarray:
        return self.model.dict_to_concentrations(data)
    
    def vector_to_dict(self, vec: np.ndarray) -> Dict[str, float]:
        return self.model.concentrations_to_dict(vec)
    
    def reactions(self, c: np.ndarray) -> np.ndarray:
        return self.model.compute_derivatives(c)

    def initial_state(
            self, 
            do_setpoint: float,
            process_id: Optional[str] = None,
            use_calibration: bool = False,
            process_config: Optional[Dict[str, Any]] = None
        ) -> Dict[str, float]:
        """
        Crée l'état initial du procédé

        Args:
            do_setpoint (float): Consigne d'oxygène dissous
            process_id (Optional[str], optional): ID du procédé. Defaults to None.
            use_calibration (bool, optional): Utiliser la calibration si disponible. Defaults to False.

        Returns:
            Dict[str, float]: Etat initial complet
        """
        if use_calibration and process_id:
            steady_state = self._load_steady_state(process_id, process_config)
            if steady_state:
                logger.info(
                    f"Etat initial chargé depuis calibration pour {process_id}"
                )

                if self.name == 'ASM1':
                    steady_state['so'] = do_setpoint
                else:
                    steady_state['so2'] = do_setpoint

                return steady_state
            
        logger.debug(
            f"Etat initial par défaut pour {self.name} "
            f"(pas de calibration ou use_calibration=False)"
        )

        return self._get_default_initial_state(do_setpoint)
    
    def _load_steady_state(self, process_id: str, process_config: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, float]]:
        """
        Charge le steady-state depuis la calibration en cache

        Args:
            process_id (str): ID du procédé

        Returns:
            Optional[Dict[str, float]]
        """
        try:
            cache = CalibrationCache()

            config_hash = None
            if process_config:
                comparator = ConfigurationComparator()
                config_hash = comparator.compute_hash(process_config)
                logger.debug(f"Hash de configuration calculé : {config_hash[:8]}")

            cached = cache.load(process_id, f"{self.name}Model", config_hash)

            if cached is None:
                logger.debug(
                    f"Pas de calibration trouvée pour {process_id}/{self.name}Model"
                )
                return None
            else:
                steady_states = cached.steady_states

            if not steady_states:
                logger.warning(
                    f"Fichier de calibration vide pour {process_id}"
                )
                return None
            
            steady_state = list(steady_states.values())[0]

            if not isinstance(steady_state, dict):
                logger.error(
                    f"Steady-state invalide pour {process_id} : "
                    f"attendu dict, reçu {type(steady_state)}" 
                )
                return None
            
            logger.info(
                f"Steady-state chargé pour {process_id} : "
                f"{len(steady_state)} paramètres"
            )

            return steady_state
        except Exception as e:
            logger.warning(
                f"Erreur lors du chargement du steady-state pour {process_id} : {e}"
            )
            return None
        
    def _get_default_initial_state(
            self,
            do_setpoint: float
        ) -> Dict[str, float]:
        """
        Fournit les valeurs par défaut d'initialisation
        
        Args:
            do_setpoint : Consigne DO (mg/L)
            
        Returns:
            Dict[str, float] : État initial
        """        
        if self.name in ['ASM2D', 'ASM2d']:
            return {
                'so2': do_setpoint,
                'sf': 10.0,
                'sa': 5.0,
                'snh4': 2.0,
                'sno3': 5.0,
                'spo4': 1.0,
                'si': 30.0,
                'salk': 5.0,
                'sn2': 0.0,
                'xi': 25.0,
                'xs': 100.0,
                'xh': 1500.0,
                'xpao': 200.0,
                'xpp': 50.0,
                'xpha': 10.0,
                'xaut': 80.0,
                'xtss': 2000.0,
                'xmeoh': 50.0,
                'xmep': 0.0
            }
        
        elif self.name == 'ASM3':
            return {
                "so2": do_setpoint,
                "si": 30.0,
                "ss": 5.0,
                "snh4": 1.0,
                "sn2": 1.0,
                "snox": 0.5,
                "salk": 7.0,
                "xi": 25.0,
                "xs": 125.0,
                "xh": 2500.0,
                "xsto": 500.0,
                "xa": 300.0,
                "xss": 5.0,
            }
        else:
            return {
                'si': 30.0,
                'ss': 5.0, 
                'xi': 25.0, 
                'xs': 100.0,
                'xbh': 2500.0, 
                'xba': 150.0, 
                'xp': 450.0,
                'so': do_setpoint, 
                'sno': 5.0, 
                'snh': 2.0,
                'snd': 1.0, 
                'xnd': 5.0, 
                'salk': 7.0
            }
    
    def get_component_names(self) -> list:
        """Retourne la liste des noms de composants"""
        return self.model.get_component_names()
