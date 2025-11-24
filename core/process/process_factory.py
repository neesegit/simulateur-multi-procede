"""
Factory pour créer les ProcessNodes à partir de la configuration

Rôle :
- Instancier les ProcessNodes selon leur type
- Gérer les connexions entre procédés
- Centraliser la logique de création
"""
from typing import Dict, Any, List
import logging

from core.process.process_node import ProcessNode
from core.process.process_registry import ProcessRegistry
from core.connection.connection_manager import ConnectionManager


logger = logging.getLogger(__name__)

class ProcessFactory:
    """
    Factory pour créer et connecter les ProcessNodes
    """

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
        registry = ProcessRegistry.get_instance()

        return registry.create_process(
            process_type=proc_config['type'],
            node_id=proc_config['node_id'],
            name=proc_config['name'],
            config=proc_config.get('config', {})
        )
    
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
        ProcessFactory._setup_connections(processes, config)

        logger.info(f"{len(processes)} procédé(s) crée(s)")

        return processes
    
    @staticmethod
    def _setup_connections(processes: List[ProcessNode],
                           config: Dict[str, Any]) -> None:
        """
        Configure les connexions entre ProcessNodes

        Args:
            processes (List[ProcessNode]): Liste des ProcessNodes
            configs (List[Dict[str, Any]]): Configurations correspondantes
        """
        conn_manager = ConnectionManager()
        # Crée un mapping node_id -> ProcessNode
        process_map = {p.node_id: p for p in processes}

        if 'connections' not in config or not config['connections']:
            ProcessFactory._create_sequentiel_chain(processes, conn_manager)
            logger.info("\n" + conn_manager.visualize_ascii())
            return 

        for conn_config in config.get('connections', []):
            source = conn_config['source']
            target = conn_config['target']
            fraction = conn_config.get('fraction', 1.0)
            is_recycle = conn_config.get('is_recycle', False)

            # Ajouter au ConnectionManager
            conn_manager.add_connection(source, target, fraction, is_recycle)

            # Configurer les ProcessNodes
            if target in process_map:
                process_map[target].connect_upstream(source)
            if source in process_map:
                process_map[source].connect_downstream(target)

        # Valider
        validation = conn_manager.validate()
        if validation['errors']:
            for error in validation['errors']:
                logger.error(error)
            raise Exception("Erreurs dans le graphe de connexions")
        
        logger.info("\n"+conn_manager.visualize_ascii())
        return 
    
    @staticmethod
    def _create_sequentiel_chain(processes: List[ProcessNode],
                                 conn_manager: ConnectionManager) -> None:
        """
        Crée une chaîne sequentielle simple

        Args:
            processes (List[ProcessNode]): Liste de ProcessNodes
            conn_manager (ConnectionManager): Gestion de connexions
        """
        if not processes:
            return
        first = processes[0]
        conn_manager.add_connection('influent', first.node_id, 1.0, False)
        first.connect_upstream('influent')

        for i in range(len(processes) - 1):
            current = processes[i]
            next_proc = processes[i+1]

            conn_manager.add_connection(current.node_id, next_proc.node_id, 1.0, False)
            current.connect_downstream(next_proc.node_id)
            next_proc.connect_upstream(current.node_id)

            logger.debug(f"Chaîne séquentiel : {current.node_id} -> {next_proc.node_id}")
    
    @staticmethod
    def get_available_types() -> List[str]:
        """
        Retourne la liste des types de procédés disponibles

        Returns:
            List[str]: Liste des noms de types
        """
        registry = ProcessRegistry.get_instance()
        return registry.get_process_types()
    

        
