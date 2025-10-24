"""
Registre centralisé des procédés disponibles

Ce module charge dynamiquement les procédés depuis un fichier json et gère leur instanciation
"""
import json
import logging

from pathlib import Path
from typing import Dict, Any, List, Optional

from core.process.process_node import ProcessNode
from core.process.process_definition import ProcessDefinition

logger = logging.getLogger(__name__)

class ProcessRegistry:
    """
    Registre centralisé des types de procédés disponibles
    """

    _instance = None

    def __init__(self, catalog_path: Optional[Path]) -> None:
        if catalog_path is None:
            catalog_path = Path(__file__).parent / 'config' / 'processes_catalog.json'
        
        self.catalog_path = catalog_path
        self.processes: Dict[str, ProcessDefinition] = {}
        self.categories: Dict[str, Dict[str, str]] = {}

        self._load_catalog()

    def _load_catalog(self) -> None:
        """Charge le catalogue depuis le fichier json"""
        if not self.catalog_path.exists():
            raise FileNotFoundError(
                f"Catalogue de procédés introuvable : {self.catalog_path}"
            )
        
        with open(self.catalog_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        self.categories = data.get('categories', {})

        for proc_data in data.get('processes', []):
            definition = ProcessDefinition.from_dict(proc_data)
            self.processes[definition.type] = definition
            logger.debug(f"Procédé chargé : {definition.type} - {definition.name}")

        logger.info(f"Catalogue chargé : {len(self.processes)} procédé(s)")

    @classmethod
    def get_instance(cls, catalog_path: Optional[Path] = None) -> 'ProcessRegistry':
        """Retourne l'instance du registre"""
        if cls._instance is None:
            cls._instance = cls(catalog_path)
        return cls._instance
    
    def get_process_definition(self, process_type: str) -> ProcessDefinition:
        """Récupère la définition d'un procédé"""
        if process_type not in self.processes:
            available = ', '.join(self.processes.keys())
            raise ValueError(
                f"Type de procédé inconnu : '{process_type}'. "
                f"Type disponibles : {available}"
            )
        return self.processes[process_type]
    
    def create_process(
            self,
            process_type: str,
            node_id: str,
            name: str,
            config: Dict[str, Any]
    ) -> ProcessNode:
        """
        Crée une instance de procédé

        Args:
            process_type (str): Type du procédé
            node_id (str): Identifiant unique
            name (str): Nom descriptif
            config (Dict[str, Any]): Configuration spécifique

        Returns:
            ProcessNode: Instance de ProcessNode
        """
        definition = self.get_process_definition(process_type)
        process_class = definition.get_class()

        full_config = definition.get_default_config()
        full_config.update(config)

        instance = process_class(node_id, name, full_config)
        logger.info(f"ProcessNode crée : {name} ({process_type})")

        return instance
    
    def list_processes(self, category: Optional[str] = None) -> List[ProcessDefinition]:
        """
        Liste les procédés disponibles

        Args:
            category (Optional[str], optional): Filtrer par catégorie. Defaults to None.

        Returns:
            List[ProcessDefinition]: Liste de ProcessDefinition
        """
        processes = list(self.processes.values())
        if category:
            processes = [p for p in processes if p.category == category]

        return sorted(processes, key=lambda p: p.name)
    
    def list_categories(self) -> Dict[str, Dict[str, str]]:
        """Retourne toutes les catégories"""
        return self.categories
    
    def get_process_types(self) -> List[str]:
        """Retourne la liste des types de procédés"""
        return list(self.processes.keys())
    
    def to_cli_format(self) -> Dict[str, Dict[str, Any]]:
        """
        Convertit le registre au format attendu par CLIInterface

        Returns:
            Dict[str, Dict[str, Any]]: Dict compatible avec CLIInterface.AVAILABLE_PROCESSES
        """
        cli_format = {}

        for i, (proc_type, definition) in enumerate(self.processes.items(), 1):
            cli_format[str(i)] = {
                'type': definition.type,
                'name': definition.name,
                'description': f"{definition.description}",
                'required_params': [p.name for p in definition.required_params],
                'optional_params': [p.name for p in definition.optional_params],
                'has_model_choice': definition.has_model_choice
            }
        return cli_format
    
    def to_default_params(self) -> Dict[str, Dict[str, float]]:
        """
        Convertit le registre au format DEFAULT_PARAMS

        Returns:
            Dict[str, Dict[str, float]]: Dict compatible avec CLIInterface.DEFAULT_PARAMS
        """
        default_params = {}
        for proc_type, definition in self.processes.items():
            default_params[proc_type] = definition.get_default_config()

        return default_params
    
