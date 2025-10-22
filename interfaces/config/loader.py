"""
Chargeur de configurations

Ce module gère le chargement et la sauvegarde des fichiers de configuration
"""
import json
import yaml
from pathlib import Path
from typing import Dict, Any
import logging

from interfaces.config import ConfigDefaults, ConfigValidator

logger = logging.getLogger(__name__)

class ConfigLoader:
    """
    Charge, valide et sauvegarde les configurations de simulation
    """

    @staticmethod
    def load(path: Path) -> Dict[str, Any]:
        """
        Charge une configuration depuis un fichier

        Args:
            path (Path): Chemin vers le fichier de config

        Returns:
            Dict[str, Any]: Configuration validée avec valeurs par défaut

        Raises:
            FileNotFoundError: Si le fichier n'existe pas
            ValueError: Si la configuration est invalide
        """
        if not path.exists():
            raise FileNotFoundError(
                f"Fichier de configuration introuvable: {path}"
            )
        
        if path.suffix == '.json':
            with open(path, 'r', encoding='utf-8') as f:
                config = json.load(f)
        elif path.suffix in ['.yaml', '.yml']:
            with open(path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
        else:
            raise ValueError(
                f"Format de fichier non supporté: {path.suffix}. "
                "Utilisez .json, .yaml, .yml"
            )
        
        logger.info(f"Configuration chargée depuis {path}")

        ConfigValidator.validate(config)

        config = ConfigDefaults.apply_defaults(config)

        return config
    
    @staticmethod
    def load_multiple(
        config_dir: str,
        pattern: str = "*.json"
    ) -> Dict[str, Dict[str, Any]]:
        """
        Charge plusieurs configurations depuis un répertoire

        Args:
            config_dit (str): Répertoire contenant les configs
            pattern (str, optional): Pattern de fichier. Defaults to "*.json".

        Returns:
            Dict[str, Dict[str, Any]]: Dictionnaire {nom_fichier: config}

        Raises:
            FileNotFoundError: Si le répertoire n'existe pas
            ValueError: Si aucune configuration trouvée
        """
        dir_path = Path(config_dir)

        if not dir_path.exists():
            raise FileNotFoundError(
                f"Répertoire introuvable: {config_dir}"
            )
        
        configs = {}

        for file_path in dir_path.glob(pattern):
            try:
                config = ConfigLoader.load(file_path)
                configs[file_path.stem] = config
                logger.info(f"Configuration chargée : {file_path.name}")
            except Exception as e:
                logger.warning(
                    f"Erreur lors du chargement de {file_path.name} : {e}"
                )

        if not configs:
            raise ValueError(
                f"Aucune configuration trouvée dans {config_dir}"
                f" avec pattern {pattern}"
            )
        
        logger.info(f"{len(configs)} configration(s) chargée(s)")

        return configs
    
    @staticmethod
    def save(config: Dict[str, Any], output_path: Path) -> None:
        """
        Sauvegarde une configuration dans un fichier

        Args:
            config (Dict[str, Any]): Configuration à sauvegarder
            output_path (Path): Chemin de sauvegarde

        Raise:
            ValueError: Si le format de fichier n'est pas supporté
        """
        output_path.parent.mkdir(parents=True, exist_ok=True)

        if output_path.suffix == '.json':
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
        elif output_path.suffix in ['.yaml', '.yml']:
            with open(output_path, 'w', encoding='utf-8') as f:
                yaml.dump(
                    config,
                    f,
                    default_flow_style=False,
                    allow_unicode=True
                )
        else:
            raise ValueError(
                f"Format de fichier non supporté: {output_path.suffix}"
            )
        
        logger.info(f"Configuration sauvegardée : {output_path}")

