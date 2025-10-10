"""
Simulation Orchestrator - Cerveau du simulateur
Gère l'exécution temporelle et la coordination entre ProcessNodes
"""
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import logging
from pathlib import Path
import json

from core.databuses import DataBus, SimulationFlow, FlowData
from core.process_node import ProcessNode

logger = logging.getLogger(__name__)

class SimulationOrchestrator:
    """
    Orchestre la simulation complète d'une chaîne de traitement
    """

    def __init__(self, config: Dict[str, Any]):
        """
        Initialise l'orchestrateur

        Args:
            config (Dict[str, Any]): Configuration de la simulation contenant:
                - Simulation: paramètre temporels (start, end, timestep)
                - Processes: Liste des procédés à simuler
                - influent: caractéristiques de l'eau entrante
        """
        self.config = config
        self.logger = logging.getLogger(f"{__name__}.{config.get('name', 'sim')}")

        # Paramètres temporels
        sim_config = config.get('simulation', {})
        self.start_time = datetime.fromisoformat(sim_config.get('start_time'))
        self.end_time = datetime.fromisoformat(sim_config.get('end_time'))
        self.timestep = sim_config.get('timestep_hours', 0.1) # heures

        # Infrastructure de communication
        self.databus = DataBus()
        self.simulation_flow = SimulationFlow()

        # Liste des ProcessNodes (rempli par process_factory)
        self.process_nodes: List[ProcessNode] = []
        self.process_map : Dict[str, ProcessNode] = {}

        # Etat de la simulation
        self.current_time = self.start_time
        self.current_step = 0
        self.is_running = False

        # Résultats
        self.results: Dict[str, Any] = {
            'metadata': {
                'start_time': self.start_time.isoformat(),
                'end_time': self.end_time.isoformat(),
                'timestep': self.timestep,
                'config': config
            },
            'history': {}
        }

        self.logger.info(f"Orchestrator initialisé : {self.start_time} -> {self.end_time}, dt={self.timestep}h")

    def add_process(self, process: ProcessNode) -> None:
        """
        Ajoute un ProcessNode à la chaîne de simulation

        Args:
            process (ProcessNode): Instance de ProcessNode à ajouter
        """
        if process.node_id in self.process_map:
            raise ValueError(f"ProcessNode avec ID '{process.node_id}' déjà existant")
        
        self.process_nodes.append(process)
        self.process_map[process.node_id] = process
        self.logger.info(f"ProcessNode ajouté : {process.name} ({process.node_id})")

    def initialize(self) -> None:
        """
        Initialise tous les processNodes et prépare la simulation
        """
        self.logger.info("Initialisation de la simulation...")

        # Initialise chaque procédé
        for process in self.process_nodes:
            try:
                process.initialize()
                self.logger.debug(f"ProcessNode '{process.name}' initialisé")
            except Exception as e:
                self.logger.error(f"Erreur initialisation de '{process.name}' : {e}")
                raise

        # Prépare l'influent initial
        self._initialize_influent()
        
        self.logger.info(f"Simulation prête avec {len(self.process_nodes)} procédé(s)")
    
    def _initialize_influent(self) -> None:
        """
        Crée le FlowData initial de l'influent à partir de la config
        """
        influent_config = self.config.get('influent', {})

        # Crée le flux avec fractionnement automatique si configuré

        influent = FlowData.create_from_model(
            timestamp=self.current_time,
            flowrate=influent_config.get('flowrate', 1000.0),
            temperature=influent_config.get('temperature', 20.0),
            model_type=influent_config.get('model_type', 'ASM1'),
            auto_fractionate=influent_config.get('auto_fractionate', True),
            **influent_config.get('composition', {})
        )

        # Place l'influent dans le DataBus sous le nom 'influent'
        self.databus.write_flow('influent', influent)
        self.simulation_flow.add_flow('influent', influent)

        self.logger.info(f"Influent initialisé: Q={influent.flowrate} m^3/h, DCO={influent.cod} mg/L")

    def run(self) -> Dict[str, Any]:
        """
        Exécute la simulation complète

        Returns:
            Dict[str, Any]: Dictionnaire contenant les résultats de la simulation
        """
        self.logger.info("="*60)
        self.logger.info("Démarrage de la simulation")
        self.logger.info("="*60)

        self.is_running = True
        self.current_time = self.start_time
        self.current_step = 0

        total_steps = int((self.end_time - self.start_time).total_seconds() / 3600 / self.timestep)
        self.logger.info(f"Nombre de pas de temps : {total_steps}")

        try:
            while self.current_time < self.end_time:
                self._run_timestep()

                # Avance dans le temps
                self.current_time += timedelta(hours=self.timestep)
                self.current_step += 1

                # Log de progression
                if self.current_step % 100 == 0:
                    progress = (self.current_step / total_steps)*100
                    self.logger.info(f"Progression : {progress:.1f}% (step {self.current_step}/{total_steps})")

        except KeyboardInterrupt:
            self.logger.warning("Simulation interrompue par l'utilisateur")
            self.is_running = False

        except Exception as e:
            self.logger.error(f"Erreur durant la simulation : {e}", exc_info=True)
            self.is_running = False
            raise

        finally:
            self._finalize()

        self.logger.info("="*60)
        self.logger.info("Simulation terminée")
        self.logger.info("="*60)

        return self.results
    
    def _run_timestep(self) -> None:
        """
        Exécute un seul pas de temps de simulation
        """

        # Pour chaque ProcessNode, dans l'ordre de la chaîne
        for process in self.process_nodes:
            try:
                # Récupère les inputs depuis le DataBus
                inputs = self._get_process_inputs(process)

                # Valide les inputs
                if not process.validate_inputs(inputs):
                    raise ValueError(f"Inputs invalides pour '{process.name}'")
                
                # Exécute le traitement
                outputs = process.process(inputs, dt=self.timestep)

                # Met à jour l'état interne
                process.update_state(outputs)

                # Crée le FlowData de sortie
                output_flow = self._create_output_flow(process, outputs)

                # Ecrit dans le DataBus pour le prochain procédé
                self.databus.write_flow(process.node_id, output_flow)

                # Enregistre dans l'historique
                self.simulation_flow.add_flow(process.node_id, output_flow)

            except Exception as e:
                self.logger.error(f"Erreur dans '{process.name}' à t={self.current_time} : {e}")
                raise

    def _get_process_inputs(self, process: ProcessNode) -> Dict[str, Any]:
        """
        Récupère les inputs pour un ProcessNode depuis le DataBus

        Args:
            process (ProcessNode): ProcessNode dont on veut les inputs

        Returns:
            Dict[str, Any]: Dictionnaire des inputs
        """

        inputs = {}

        # Si le procédé a des nodes en amont, lit leurs sorties
        if process.upstream_nodes:
            # On prend le premier (cas simple)
            upstream_id = process.upstream_nodes[0]
            upstream_flow = self.databus.read_flow(upstream_id)

            if upstream_flow:
                inputs = {
                    'flow': upstream_flow,
                    'flowrate': upstream_flow.flowrate,
                    'temperature': upstream_flow.temperature,
                    'components': upstream_flow.components.copy()
                }
        else:
            # Premier procédé : lit l'influent
            influent = self.databus.read_flow('influent')
            if influent:
                inputs = {
                    'flow': influent,
                    'flowrate': influent.flowrate,
                    'temperature': influent.temperature,
                    'components': influent.components.copy()
                }
        
        return inputs
    
    def _create_output_flow(self, process: ProcessNode, outputs: Dict[str, Any]) -> FlowData:
        """
        Crée un FlowData à partir des outputs d'un ProcessNode

        Args:
            process (ProcessNode): ProcessNode source
            outputs (Dict[str, Any]): Dictionnaire des outputs

        Returns:
            FlowData: FlowData contruit
        """

        flow = FlowData(
            timestamp=self.current_time,
            flowrate=outputs.get('flowrate', 0.0),
            temperature=outputs.get('temperature', 20.0),
            model_type=outputs.get('model_type'),
            source_node=process.node_id
        )

        # Copie les composants
        if 'components' in outputs:
            flow.components = outputs['components'].copy()

        # Copie les paramètres standards s'ils existent
        for key in ['cod', 'ss', 'bod', 'tkn']:
            if key in outputs:
                setattr(flow, key, outputs[key])

        return flow
    
    def _finalize(self) -> None:
        """
        Finalise la simulation et prépare les résultats
        """
        self.logger.info("finalisation de la simulation ...")

        # Exporte l'historique
        self.results['history'] = self.simulation_flow.export_to_dict()

        # Calcule des statistiques globales
        self.results['statistics'] = self._compute_statistics()

        # Metadonnées finales
        self.results['metadata']['steps_completed'] = self.current_step
        self.results['metadata']['final_time'] = self.current_time.isoformat()

    def _compute_statistics(self) -> Dict[str, Any]:
        """
        Calcule des statistiques sur la simulation

        Returns:
            Dict[str, Any]: Dictionnaire de statistiques
        """
        stats={}

        for node_id, history in self.simulation_flow.get_all_histories().items():
            if not history:
                continue

            node_stats = {
                'num_samples': len(history),
                'avg_flowrate': sum(f.flowrate for f in history) / len(history),
                'avg_cod': sum(f.get('cod', 0) for f in history) / len(history)
            }

            stats[node_id] = node_stats

        return stats
    
    def save_results(self, output_dir: str) -> Path:
        """
        Sauvegarde les résultats de la simulation

        Args:
            output_dir (str): Répertoire de sortie

        Returns:
            Path: Chemin du fichier de résultats
        """

        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        # Nom de fichier avec timestamp
        filename = f"simulation_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        filepath = output_path/filename

        # Sauvegarde en JSON
        with open(filepath, 'w') as f:
            json.dump(self.results, f, indent=2, default=str)

        self.logger.info(f"Résultats sauvegardés : {filepath}")
        return filepath
    
    def get_process(self, node_id: str) -> Optional[ProcessNode]:
        """
        Récupère un ProcessNode par son ID

        Args:
            node_id (str): ID du procédé

        Returns:
            Optional[ProcessNode]: ProcessNode ou None
        """
        return self.process_map.get(node_id)
    
    def __repr__(self) -> str:
        return f"<SimulationOrchestrator(process={len(self.process_nodes)}, steps={self.current_step})>"