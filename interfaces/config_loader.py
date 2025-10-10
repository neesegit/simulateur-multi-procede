"""
Module de chargement et validation des configurations

Rôle :
- Charger les fichiers JSON/YAML de configuration
- Valider la structure et les valeurs
- Fournir des valeurs par défaut
"""
import json
import yaml
from pathlib import Path
from typing import Dict, Any, Optional
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class ConfigLoader:
    """
    Charge et valide les configurations de simulation
    """

    # Schéma de validation (valeurs requises)
    REQUIRED_FIELDS = {
        'simulation': ['start_time', 'end_time', 'timestep_hours'],
        'influent': ['flowrate', 'temperature', 'model_type'],
        'processes': [] # Liste, validée spéparément
    }

    @staticmethod
    def load(config_path: str) -> Dict[str, Any]:
        """
        Charge une configuration depuis un fichier

        Supporte JSON et YAML

        Args:
            config_path (str): Chemin vers le fichier de configuration

        Returns:
            Dict[str, Any]: Dictionnaire de configuration validé

        Raises:
            FileNotFoundError: Si le fichier n'existe pas
            ValueError: Si la configuration est invalide
        """
        path = Path(config_path)

        if not path.exists():
            raise FileNotFoundError(f"Fichier de configuration introuvable: {config_path}")
        
        # Charge selon l'extention
        if path.suffix == '.json':
            with open(path, 'r') as f:
                config = json.load(f)
        elif path.suffix in ['.yaml', '.yml']:
            with open(path, 'r') as f:
                config = yaml.safe_load(f)
        else:
            raise ValueError(f"Format de fichier non supporté: {path.suffix}")
        
        logger.info(f"Configuration chargée depuis {config_path}")

        # Valide la configuration
        ConfigLoader._validate(config)

        # Applique les valeurs par défaut
        config = ConfigLoader._apply_defaults(config)

        return config
    
    @staticmethod
    def _validate(config: Dict[str, Any]) -> None:
        """
        Valide la structure de la configuration

        Args:
            config (Dict[str, Any]): Configuration à valider

        Raises:
            ValueError: Si la configuration est invalide
        """
        # Vérifie les sections principales
        for section, required in ConfigLoader.REQUIRED_FIELDS.items():
            if section not in config:
                raise ValueError(f"Section manquante dans la configuration: '{section}'")
            
            # Vérifie les champs requis dans chaque section
            for field in required:
                if field not in config[section]:
                    raise ValueError(f"Champ manquant dans '{section}': '{field}'")
                
        
        # Valide les dates
        try:
            start = datetime.fromisoformat(config['simulation']['start_time'])
            end = datetime.fromisoformat(config['simulation']['end_time'])
            if end <= start:
                raise ValueError("end_time doit être après start_time")
        except Exception as e:
            raise ValueError(f"Erreur dans les dates de simulation: {e}")
        
        # Valide le timestep
        dt = config['simulation']['timestep_hours']
        if dt <= 0 or dt > 24:
            raise ValueError(f"timestep_hours invalide: {dt} (doit être entre 0 et 24)")
        
        # Valide la liste des procédés
        if not isinstance(config['processes'], list):
            raise ValueError("'processes' doit être une liste")
        
        if len(config['processes']) == 0:
            raise ValueError("Au moins un procédé doit être défini")
        
        # Valide chaque procédé
        for i, proc in enumerate(config['processes']):
            if 'node_id' not in proc:
                raise ValueError(f"Procédé {i}: 'node_id' manquant")
            if 'type' not in proc:
                raise ValueError(f"Procédé {i}: 'type' manquant")
            if 'name' not in proc:
                raise ValueError(f"Procédé {i}: 'name' manquant")
            
        logger.info("Configuration validée avec succès")
        
    @staticmethod
    def _apply_defaults(config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Applique les valeurs par défaut pour les champs optionnels

        Args:
            config (Dict[str, Any]): Configuration

        Returns:
            Dict[str, Any]: Configuration avec valeurs par défaut appliquées
        """
        # Nom par défaut
        if 'name' not in config:
            config['name'] = f"simulation_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        # Description par défaut
        if 'description' not in config:
            config['description'] = "Simulation générée automatiquement"

        # Valeurs par défaut pour l'influent
        influent = config['influent']
        influent.setdefault('auto_fractionate', True)
        influent.setdefault('composition', {})

        # Valeurs par défaut pour chauqe procédé
        for proc in config['processes']:
            proc.setdefault('config', {})

        return config
    
    @staticmethod
    def load_multiple(config_dir: str, pattern: str="*.json") -> Dict[str, Dict[str, Any]]:
        """
        Charge plusieurs configuration depuis un répertoire

        Args:
            config_dir (str): Répertoire contenant les configs
            pattern (str, optional): Pattern de fichiers (ex : "*.json", "scenario_*.yaml"). Defaults to "*.json".

        Returns:
            Dict[str, Dict[str, Any]]: Dictionnaire {nom_fichier: config}
        """
        config_path = Path(config_dir)

        if not config_path.exists():
            raise FileNotFoundError(f"Répertoire introuvable : {config_dir}")
        
        configs = {}

        for file_path in config_path.glob(pattern):
            try:
                config = ConfigLoader.load(str(file_path))
                configs[file_path.stem] = config
                logger.info(f"Configuration chargée : {file_path.name}")
            except Exception as e:
                logger.warning(f"Erreur lors du chargement de {file_path.name} : {e}")

        if not configs:
            raise ValueError(f"Aucune configuration trouvée dans {config_dir} avec pattern {pattern}")
        
        logger.info(f"{len(configs)} configuration(s) chargée(s)")
        return configs
    
    @staticmethod
    def save(config: Dict[str, Any], output_path: str) -> None:
        """
        Sauvegarde une configuration dans un fichier

        Args:
            config (Dict[str, Any]): Configuration à sauvegarder
            output_path (str): Chemin de sortie
        """
        path = Path(output_path)
        path.parent.mkdir(parents=True, exist_ok=True)

        # Sauvegarde selon l'extension
        if path.suffix == '.json':
            with open(path, 'w') as f:
                json.dump(config, f, indent=2)
        elif path.suffix in ['.yaml', '.yml']:
            with open(path, 'w') as f:
                yaml.dump(config, f, default_flow_style=False)
        else:
            raise ValueError(f"Format de fichier non supporté : {path.suffix}")
        
        logger.info(f"Configuration sauvegardée : {output_path}")

    @staticmethod
    def create_default_config(output_path: Optional[str] = None) -> Dict[str, Any]:
        """
        Crée une configuration par défaut

        Args:
            output_path (Optional[str], optional): Si fourni, sauvegarde la config à ce chemin

        Returns:
            Dict[str, Any]: Configuration par défaut
        """
        default_config = {
            "name": "simulation_default",
            "description": "Configuration par défaut ASM1",
            "simulation": {
                "start_time": "2025-01-01T00:00:00",
                "end_time": "2025-01-02T00:00:00",
                "timestep_hours": 0.1
            },
            "influent": {
                "flowrate": 1000.0,
                "temperature": 20.0,
                "model_type": "ASM1",
                "auto_fractionate": True,
                "composition": {
                    "cod": 500.0,
                    "ss": 250.0,
                    "tkn": 40.0,
                    "nh4": 28.0,
                    "no3": 0.5,
                    "po4": 8.0,
                    "alkalinity": 6.0
                }
            },
            "processes": [
                {
                    "note_id": "aeration_tank",
                    "type": "ASM1Process",
                    "name": "Bassin d'aération",
                    "config": {
                        "volume": 5000.0,
                        "depth": 4.0,
                        "dissolved_oxygen_setpoint": 2.0,
                        "recycle_ratio": 1.0,
                        "waste_ratio": 0.01
                    }
                }
            ]
        }

        if output_path:
            ConfigLoader.save(default_config, output_path)

        return default_config