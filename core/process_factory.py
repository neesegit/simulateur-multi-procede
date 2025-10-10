"""
Factory pour créer les ProcessNodes à partir de la configuration

Rôle :
- Instancier les ProcessNodes selon leur type
- Gérer les connexions entre procédés
- Centraliser la logique de création
"""
from typing import Dict, Any, List
import logging

from core.process_node import ProcessNode
from processes.asm1_process import ASM1Process

logger = logging.getLogger(__name__)

class ProcessFactory:
    """
    Factory pour créer et connecter les ProcessNodes
    """

    # Registre des types de procédés disponibles
    PROCESS_TYPES = {
        'ASM1Process': ASM1Process,
        # Ajoutez ici d'autres procédés :
        # 'NOMProcess' : NOMProcess
    }

    @staticmethod
    def create_process(proc_config: Dict[str, Any]) -> ProcessNode:
        """
        Crée une instance de ProcessNode selon sa configuration

        Args:
            proc_config (Dict[str, Any]): Configuration du procédé contenant :
                                            - type: Type de procédé (ex : 'ASM1Process')
                                            - node_id: Identifiant unique
                                            - name: Nom descriptif
                                            - config: Paramètres spécifiques

        Returns:
            ProcessNode: Instance de ProcessNode
        
        Raises:
            ValueError: Si le type de procédé est inconnu
        """
        proc_type = proc_config['type']
        node_id = proc_config['node_id']
        name = proc_config['name']
        params = proc_config.get('config', {})

        # Vérifie que le type est supporté
        if proc_type not in ProcessFactory.PROCESS_TYPES:
            available = ', '.join(ProcessFactory.PROCESS_TYPES.keys())
            raise ValueError(
                f"Type de procédé inconnu : '{proc_type}'."
                f"Types disponibles : {available}"
            )
        
        # Instancie la classe appropriée
        process_class = ProcessFactory.PROCESS_TYPES[proc_type]
        process = process_class(node_id, name, params)

        logger.info(f"ProcessNode créé : {name} ({proc_type})")

        return process
    
    @staticmethod
    def create_from_config(config: Dict[str, Any]) -> List[ProcessNode]:
        """
        Crée tous les ProcessNodes à partir d'une configuration complète

        Args:
            config (Dict[str, Any]): Configuration complète contenant la liste 'processes'

        Returns:
            List[ProcessNode]: Liste des ProcessNodes crées
        """
        processes_config = config.get('processes', [])

        if not processes_config:
            raise ValueError("Aucun procédé défini dans la configuration")
        
        processes = []

        for proc_config in processes_config:
            process = ProcessFactory.create_process(proc_config)
            processes.append(process)

        # Configure les connexions si spécifiées
        ProcessFactory._setup_connections(processes, processes_config)

        logger.info(f"{len(processes)} procédé(s) crée(s)")

        return processes
    
    @staticmethod
    def _setup_connections(processes: List[ProcessNode],
                           configs: List[Dict[str, Any]]) -> None:
        """
        Configure les connexions entre ProcessNodes

        Les connexions peuvent être définies dans la config comme :
        {
            "node_id": "aeration",
            "connections": {
                "upstream": ["anoxie"],
                "downstream": ["settler"]
            }
        }

        Args:
            processes (List[ProcessNode]): Liste des ProcessNodes
            configs (List[Dict[str, Any]]): Configurations correspondantes
        """
        # Crée un mapping node_id -> ProcessNode
        process_map = {p.node_id: p for p in processes}

        # Pour chauqe procédé
        for process, config in zip(processes, configs):
            connections = config.get('connections', {})

            # Connexion en amont
            for upstream_id in connections.get('upstream', []):
                if upstream_id in process_map:
                    process.connect_upstream(upstream_id)
                    process_map[upstream_id].connect_downstream(process.node_id)
                    logger.debug(f"Connexion: {upstream_id} -> {process.node_id}")
                elif upstream_id != 'influent':
                    logger.warning(f"Procédé upstream introuvable : {upstream_id}")
            
            # Connexion en aval
            for downstream_id in connections.get('downstream', []):
                if downstream_id in process_map:
                    process.connect_downstream(downstream_id)
                    process_map[downstream_id].connect_upstream(process.node_id)
                    logger.debug(f"Connexion : {process.node_id} -> {downstream_id}")
                else:
                    logger.warning(f"Procédé downstream introuvable : {downstream_id}")
        
        # Si aucune connexion n'est définie, oncrée une chaîne séquentielle
        if all(not p.upstream_nodes and not p.downstream_nodes for p in processes):
            logger.info("Aucune connexion définie, création d'une chaîne séquentielle")
            ProcessFactory._create_sequential_chain(processes)

    @staticmethod
    def _create_sequential_chain(processes: List[ProcessNode]) -> None:
        """
        Crée une chaîne séquentielle simple : P1 -> P2 -> P3 -> ...

        Args:
            processes (List[ProcessNode]): Liste des ProcessNodes
        """
        for i in range(len(processes) -1):
            current = processes[i]
            next_proc = processes[i+1]

            current.connect_downstream(next_proc.node_id)
            next_proc.connect_upstream(current.node_id)

            logger.debug(f"Chaîne séquentielle : {current.node_id} -> {next_proc.node_id}")

    @staticmethod
    def register_process_type(name: str, process_class: type) -> None:
        """
        Enregistre un nouveau type de ProcessNode

        Permet d'ajouter des procédés personnalisés sans modifier ce fichier

        Args:
            name (str): Nom du type (ex : 'CustomProcess')
            process_class (type): Classe héritant de ProcessNode

        Example:
            >>> ProcessFactory.register_process_type('MyProcess', MyProcess)
            >>> # Maintenant 'MyProcess' peut être utilisé dans les configs
        """
        if not issubclass(process_class, ProcessNode):
            raise TypeError(f"{process_class} doit hériter de ProcessNode")
        
        ProcessFactory.PROCESS_TYPES[name] = process_class
        logger.info(f"Type de procédé enregistré : {name}")
    
    @staticmethod
    def get_available_types() -> List[str]:
        """
        Retourne la liste des types de procédés disponibles

        Returns:
            List[str]: Liste des noms de types
        """
        return list(ProcessFactory.PROCESS_TYPES.keys())
    

        
