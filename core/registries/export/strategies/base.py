"""Classe de base abstraite pour les stratégies d'export"""
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Dict, Any


class ExportStrategy(ABC):
    """Interface pour les stratégies d'export"""

    @property
    @abstractmethod
    def format_name(self) -> str:
        """Nom du format (ex: 'csv', 'json', 'excel')"""
        pass

    @property
    @abstractmethod
    def file_extension(self) -> str:
        """Extension de fichier (ex: '.csv', '.json')"""
        pass

    @abstractmethod
    def export(self, results: Dict[str, Any], output_path: Path, **kwargs) -> Path:
        """Exporte les résultats. Retourne le Path du fichier créé."""
        pass

    @abstractmethod
    def supports_node(self, node_type: str) -> bool:
        """Vérifie si ce format supporte un type de noeud"""
        pass
