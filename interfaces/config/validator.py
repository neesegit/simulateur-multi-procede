"""
Validateur de configurations

Ce module contient toute la logique de validation des configurations
"""
from typing import Dict, Any, Callable, List
import logging
from datetime import datetime

from .schema.config_schema import ConfigSchema

logger = logging.getLogger(__name__)

class ConfigValidator:
    """
    Valide la structure et les valeurs d'une configuration
    """

    # ===================================
    # Point d'entrée principal
    # ==================================

    @staticmethod
    def validate(config: Dict[str, Any]) -> None:
        """Valide la structure complète de la configuration"""
        logger.info("Validation de la configuration ...")

        sections: Dict[str, Callable] = {
            'simulation': ConfigValidator._validate_simulation,
            'influent': ConfigValidator._validate_influent,
            'processes': ConfigValidator._validate_processes,
        }

        missing = [s for s in sections if s not in config]
        if missing:
            raise ValueError(f"Sections manquantes : {missing}")
        
        for name, validator in sections.items():
            logger.debug(f"- Validation de la section '{name}'")
            validator(config[name])

        if 'connections' in config:
            ConfigValidator._validate_connections(config['connections'], config['processes'])

        logger.info("Configuration validée avec succès")

    # ===================================
    # Validation des sections
    # ===================================

    @staticmethod
    def _validate_simulation(sim: Dict[str, Any]) -> None:
        """Valide la section 'simulation'"""
        ConfigValidator._validate_required_fields(sim, "simulation")

        rules = {
            'start_time': ConfigValidator._validate_iso_datetime,
            'end_time': ConfigValidator._validate_iso_datetime,
            'timestep_hours': lambda v: ConfigValidator._check_range(v, 'timestep_hours')
        }

        ConfigValidator._apply_rules(sim, rules)
        start = datetime.fromisoformat(sim["start_time"])
        end = datetime.fromisoformat(sim["end_time"])
        if end <= start:
            raise ValueError("end_time doit être après start_time")
        
    @staticmethod
    def _validate_influent(influent: Dict[str, Any]) -> None:
        """Valide la section 'influent'"""
        ConfigValidator._validate_required_fields(influent, 'influent')

        rules = {
            'flowrate': lambda v: ConfigValidator._check_range(v, 'flowrate'),
            'temperature': lambda v: ConfigValidator._check_range(v, 'temperature')
        }

        ConfigValidator._apply_rules(influent, rules)

    @staticmethod
    def _validate_processes(processes: list) -> None:
        """Valide la section 'processes'"""
        if not isinstance(processes, list):
            raise ValueError("'processes' doit être une liste")
        if not processes:
            raise ValueError("Au moins un procédé doit être défini")
        
        node_ids = set()
        for i, proc in enumerate(processes):
            ConfigValidator._validate_single_process(proc, i)
            node_id = proc['node_id']
            if node_id in node_ids:
                raise ValueError(f"Procdé {i}: node_id dupliqué : '{node_id}")
            node_ids.add(node_id)

    @staticmethod
    def _validate_single_process(proc: Dict[str, Any], index: int) -> None:
        """Valide un procédé individuel"""
        ConfigValidator._validate_required_fields(proc, 'process', index)
        if not ConfigSchema.is_valid_process_type(proc['type']):
            logger.warning(
                f"Procédé {index}: Type non reconnu : '{proc['type']}'. "
                f"Types connus : {ConfigSchema.get_supported_process_types()}"
            )
        if "config" in proc:
            ConfigValidator._validate_process_config(proc['config'], index)

    @staticmethod
    def _validate_process_config(config: Dict[str, Any], index: int) -> None:
        """Valide la sous-configuration d'un procédé"""
        rules = {
            'volume': lambda v: ConfigValidator._check_range(v, 'volume', prefix=f"Procédé {index}"),
            'area': lambda v: ConfigValidator._check_range(v, 'area', prefix=f"Procédé {index}")
        }
        ConfigValidator._apply_rules(config, rules)

    @staticmethod
    def _validate_connections(connections: list, processes: list) -> None:
        """Valide les connexions entre procédés"""
        if not isinstance(connections, list):
            raise ValueError("'connections' doit être une liste")
        
        valid_node_ids = {proc['node_id'] for proc in processes}
        valid_node_ids.add('influent')

        for i, conn in enumerate(connections):
            for key in ['source', 'target']:
                if key not in conn:
                    raise ValueError(f"Connexion {i}: '{key}' manquant")
                
            source, target = conn['source'], conn['target']
            if source not in valid_node_ids:
                raise ValueError(f"Connexion {i}: source inconnue : '{source}'")
            if target not in valid_node_ids:
                raise ValueError(f"Connexion {i}: target inconnue : '{target}'")
            
            if 'fraction' in conn:
                fraction = conn['fraction']
                if not (0 < fraction <= 1.0):
                    raise ValueError(f"Connexion {i}: fraction invalide : {fraction}")


    # ====================================
    # Outils de validation génériques
    # ====================================

    @staticmethod
    def _validate_required_fields(section: Dict[str, Any], name: str, index: int | None = None) -> None:
        """Vérifie les champs requis d'une section"""
        required = ConfigSchema.get_required_fields_for_section(name)
        for field in required:
            if field not in section:
                prefix = f"Procédé {index}: " if index is not None else ""
                raise ValueError(f"{prefix}Champ manquant dans '{name}': '{field}'")
    
    @staticmethod
    def _apply_rules(data: Dict[str, Any], rules: Dict[str, Callable]) -> None:
        """Applique un ensemble de règles à un dictionnaire"""
        for field, check_fn in rules.items():
            if field in data:
                check_fn(data[field])

    @staticmethod
    def _check_range(value: float, field: str, prefix: str = "") -> None:
        """Vérifie qu'une valeur est dans la palge autorisée"""
        rng = ConfigSchema.get_value_range(field)
        if rng is None:
            logger.debug(f"{prefix}{field}: pas de contrainte de plage définie")
            return
        
        min_val, max_val = rng
        if not (min_val < value <= max_val):
            raise ValueError(
                f"{prefix}{field} invalide : {value} doit être compris entre {min_val} et {max_val}"
            )
        
    @staticmethod
    def _check_enum(value: str, valid_values: List[str], field: str) -> None:
        """Vérifie qu'une valeur appartient à un ensemble"""
        if value not in valid_values:
            raise ValueError(f"{field} invalide : '{value}'. Attendu : {valid_values}")
        
    @staticmethod
    def _validate_iso_datetime(value: str) -> None:
        """Vérifie qu'une chaîne est une date ISO valide"""
        try:
            datetime.fromisoformat(value)
        except Exception:
            raise ValueError(
                f"Format de date invalide : '{value}'. Utilisez ISO 8601 "
                "(ex : '2025-01-01T00:00:00')"
            )