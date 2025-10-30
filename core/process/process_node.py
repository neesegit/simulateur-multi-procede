"""
Classe de base ProcessNode pour tous les procédés de traitement
Chauqe procédé hérite de cette classe et implémente sa logique spécifique
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List
import logging

class ProcessNode(ABC):
    """
    Classe abstraite représentant un noeud de procédé dans la chaine de traitement
    """

    def __init__(self, node_id: str, name: str, config: Dict[str, Any]):
        """
        Initialise un noeud de procédé

        Args :
            node_id : Identifiant unique du noeud
            name : Nom descriptif du procédé
            config : Configuration spécifique du procédé
        """
        self.node_id = node_id
        self.name = name
        self.config = config
        self.logger = logging.getLogger(f"{__name__}.{node_id}")

        # Etat interne du procédé
        self.state: Dict[str, Any] = {}
        self.inputs: Dict[str, Any] = {}
        self.outputs: Dict[str, Any] = {}

        # Connexions avec d'autres noeuds
        self.upstream_nodes: List[str] = []
        self.downstream_nodes: List[str] = []

        # Performance
        self.metrics: Any = {}

        self.logger.info(f"ProcessNode '{name}' ({node_id}) initialisé")

    @abstractmethod
    def initialize(self) -> None:
        """
        Initialise l'état interne du procédé
        """
        pass

    @abstractmethod
    def process(self, inputs: Dict[str, Any], dt: float) -> Dict[str, Any]:
        """
        Traite les données d'entrée pour un pas de temps donné

        Args :
            inputs : Données d'entrée (débit, concentrations ...)
            dt: Pas de temps de simulation
        
        Returns :
            Dictionnaire contenant les sorties du procédés
        """
        pass

    @abstractmethod
    def update_state(self, outputs: Dict[str, Any]) -> None:
        """
        Met à jour l'état interne du procédé après traitement

        Args :
            outputs : Sorties calculées par la méthode process()
        """
        pass

    def validate_inputs(self, inputs: Dict[str, Any]) -> bool:
        """
        Vérifie que les entrées sont valides

        Args :
            inputs : Données d'entrée à valider
        
        Returns :
            True si valide, False sinon
        """
        required_keys = self.get_required_inputs()
        for key in required_keys:
            if key not in inputs:
                self.logger.error(f"Entrée manquante: {key}")
                return False
            if inputs[key] is None:
                self.logger.error(f"Entrée nulle: {key}")
                return False
        return True

    @abstractmethod
    def get_required_inputs(self) -> List[str]:
        """
        Retourne la liste des clés d'entrée requises
        
        Returns :
            Liste des noms de paramètres d'entrée nécessaires
        """
        pass

    def needs_fractionation(self, inputs: Dict[str, Any]) -> bool:
        """
        Vérifie si l'input nécessite un fractionnement

        Args:
            inputs (Dict[str, Any]): Données d'entrée

        Returns:
            bool: True si fractionnement nécessaire
        """
        flow = inputs.get('flow')
        if not flow:
            return False
        if flow.has_model_components():
            return False
        
        return flow.cod > 0 or flow.ss > 0 or flow.tkn > 0
    
    def fractionate_input(self, inputs: Dict[str, Any], target_model: str = 'ASM1') -> Dict[str, Any]:
        """
        Fractionne l'input si nécessaire

        Args:
            inputs (Dict[str, Any]): Données d'entrée brutes
            target_model (str, optional): Modèle cible. Defaults to 'ASM1'.

        Returns:
            Dict[str, Any]: Inputs avec composants fractionnés
        """
        if not self.needs_fractionation(inputs):
            self.logger.debug("Fractionnement on nécessaire")
            return inputs
        
        flow = inputs['flow']

        self.logger.info(f"Fractionnement en cours vers {target_model}...")
        if target_model == 'ASM1':
            from models.asm1.fraction import ASM1Fraction

            measured = flow.extract_measured()
            try:
                fractionated = ASM1Fraction.fractionate(**measured)
                fractionated_flow = flow.copy()
                fractionated_flow.components.update(fractionated)

                inputs['flow'] = fractionated_flow
                inputs['components'] = fractionated_flow.components

                self.logger.info(f"Fractionnement réussi : {len(fractionated)} composants")
            except Exception as e:
                self.logger.error(f"Erreur de fractionnement : {e}")
                raise
        elif target_model.upper() == 'ASM2D':
            from models.asm2d.fraction import ASM2dFraction

            measured = flow.extract_measured()
            try:
                fractionated = ASM2dFraction.fractionate(**measured)
                fractionated_flow = flow.copy()
                fractionated_flow.components.update(fractionated)

                inputs['flow'] = fractionated_flow
                inputs['components'] = fractionated_flow.components

                self.logger.info(f"Fractionnement réussi : {len(fractionated)} composants")
            except Exception as e:
                self.logger.error(f"Erreur de fractionnement : {e}")
                raise
        else:
            raise ValueError(f"Modèle non supporté : {target_model}")
        return inputs

    def get_outputs(self) -> Dict[str, Any]:
        """
        Retourne les sorties actuelles du procédé

        Returns :
            Dictionnaire des valeurs de sortie
        """
        return self.outputs.copy()
    
    def get_state(self) -> Dict[str, Any]:
        """
        Retourne l'état actuel du procédé

        Returns : 
            Dictionnaire de l'état interne
        """
        return self.state.copy()
    
    def get_metrics(self) -> Dict[str, float]:
        """
        Retourne les métriques de performance du procédé

        Returns :
            Dictionnaire des métriques calculées
        """
        return self.metrics.copy()
    
    def connect_upstream(self, node_id: str) -> None:
        """
        Connecte un noeud en amont

        Args :
            node_id : ID du noeud à connecter en amont
        """
        if node_id not in self.upstream_nodes:
            self.upstream_nodes.append(node_id)
            self.logger.debug(f"Noeud {node_id} connecté en amont")

    def connect_downstream(self, node_id: str) -> None:
        """
        Connecte un noeud en aval

        Args :
            node_id : ID du noeud à connecter en aval
        """
        if node_id not in self.downstream_nodes:
            self.downstream_nodes.append(node_id)
            self.logger.debug(f"Noeud {node_id} connecté en aval")
    
    def reset(self) -> None:
        """
        Réinitialise le procédé à son état initial
        """
        self.state.clear()
        self.inputs.clear()
        self.outputs.clear()
        self.metrics.clear()
        self.initialize()
        self.logger.info(f"ProcessNode '{self.name}' réinitialisé")

    def __repr__(self) -> str:
        return f"<ProcessNode(id={self.node_id}, name={self.name})>"