"""
Système d'export modulaire et extensible
"""
from typing import Dict, Any, Optional
from pathlib import Path
from abc import ABC, abstractmethod
import logging

logger = logging.getLogger(__name__)

class ExportStrategy(ABC):
    """Interface pour les statégies d'export"""

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
    def export(
        self,
        results: Dict[str, Any],
        output_path: Path,
        **kwargs
    ) -> Path:
        """
        Exporte les résultats

        Returns:
            Path du fichier créé
        """
        pass

    @abstractmethod
    def supports_node(self, node_type: str) -> bool:
        """Vérifie si ce format supporte un type de noeud"""
        pass

class CSVExportStrategy(ExportStrategy):
    """Export au format CSV"""

    @property
    def format_name(self) -> str:
        return "CSV"
    
    @property
    def file_extension(self) -> str:
        return ".csv"
    
    def export(
            self,
            results: Dict[str, Any],
            output_path: Path,
            **kwargs
    ) -> Path:
        """Exporte en CSV"""
        import pandas as pd

        history = results.get('history', {})
        node_id = kwargs.get('node_id')

        if node_id and node_id in history:
            flows = history[node_id]
            data = []

            for flow in flows:
                row = {
                    'timestamp': flow.get('timestamp'),
                    'flowrate': flow.get('flowrate'),
                    'temperature': flow.get('temperature'),
                    **flow.get('components', {})
                }
                data.append(row)

            df = pd.DataFrame(data)
            filepath = output_path / f"{node_id}_results.csv"
            df.to_csv(filepath, index=False)

            return filepath
        raise ValueError(f"Node {node_id} not found in results")
    
    def supports_node(self, node_type: str) -> bool:
        return True
    
class JSONExportStrategy(ExportStrategy):
    """Export au format JSON"""

    @property
    def format_name(self) -> str:
        return "JSON"
    
    @property
    def file_extension(self) -> str:
        return ".json"
    
    def export(self, results: Dict[str, Any], output_path: Path, **kwargs) -> Path:
        """Exporte en JSON"""
        import json

        filepath = output_path / f"{kwargs.get('name', 'simulation')}_full.json"

        with open(filepath, 'w') as f:
            json.dump(results, f, indent=2, default=str)

        return filepath
    
    def supports_node(self, node_type: str) -> bool:
        return True
    
class ExcelExportStrategy(ExportStrategy):
    """Export au format Excel avec plusieurs feuilles"""

    @property
    def format_name(self) -> str:
        return "Excel"
    
    @property
    def file_extension(self) -> str:
        return ".xlsx"
    
    def export(self, results: Dict[str, Any], output_path: Path, **kwargs) -> Path:
        """Exporte en Excel"""
        import pandas as pd

        filepath = output_path / f"{kwargs.get('name', 'simulation')}_results.xlsx"

        with pd.ExcelWriter(filepath, engine='openpyxl') as writer:
            metadata = results.get('metadata', {})
            pd.DataFrame([metadata]).to_excel(writer, sheet_name='Metadata', index=False)

            history = results.get('history', {})
            for node_id, flows in history.items():
                if not flows:
                    continue

                data = []
                for flow in flows:
                    row = {
                        'timestamp': flow.get('timestamp'),
                        'flowrate': flow.get('flowrate'),
                        **flow.get('components', {})
                    }
                    data.append(row)

                df = pd.DataFrame(data)

                sheet_name = node_id[:31]
                df.to_excel(writer, sheet_name=sheet_name, index=False)

        return filepath
    
    def supports_node(self, node_type: str) -> bool:
        return True
    
class ParquetExportStrategy(ExportStrategy):
    """Export au format Parquet (efficace pour big data)"""

    @property
    def format_name(self) -> str:
        return "Parquet"
    
    @property
    def file_extension(self) -> str:
        return ".parquet"
    
    def export(self, results: Dict[str, Any], output_path: Path, **kwargs) -> Path:
        """Exporte en Parquet"""
        import pandas as pd

        node_id = kwargs.get('node_id')
        history = results.get('history', {})

        if node_id not in history:
            raise ValueError(f"Node {node_id} not found")
        
        flows = history[node_id]
        data = []

        for flow in flows:
            row = {
                'timestamp': flow.get('timestamp'),
                'flowrate': flow.get('flowrate'),
                **flow.get('components', {})
            }
            data.append(row)

        df = pd.DataFrame(data)
        filepath = output_path / f"{node_id}_results.parquet"
        df.to_parquet(filepath, index=False, compression='snappy')

        return filepath
    
    def supports_node(self, node_type: str) -> bool:
        return True

class ExportRegistry:
    """Registre centralisé des stratégies d'export"""

    _instance = None

    def __init__(self):
        self._strategies: Dict[str, ExportStrategy] = {}
        self._default_export = set()
        self._register_default_strategies()

    @classmethod
    def get_instance(cls) -> 'ExportRegistry':
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance
    
    def _register_default_strategies(self):
        """Enregistre les stratégies par défaut"""
        self.register(CSVExportStrategy(), True)
        self.register(JSONExportStrategy(), True)

    def register(self, strategy: ExportStrategy, default=False):
        """Enregistre une stratégie d'export"""
        key = strategy.format_name.lower()
        if key in self._strategies:
            raise ValueError(f"Export type '{key}' is already registered")
        self._strategies[strategy.format_name.lower()] = strategy
        if default:
            self._default_export.add(key)
        logger.debug(f"Stratégie d'export enregistrée : {strategy.format_name}")

    def get_strategy(self, format_name: str) -> ExportStrategy:
        """Récupère la stratégie pour un type d'export"""
        key = format_name.lower()

        if key not in self._strategies:
            raise ValueError(
                f"Export type '{key}' is not registered. "
                "Available exports: "
                f"{list(self._strategies.keys())}"
            )
        
        return self._strategies[key]

    def get_available_formats(self) -> list[str]:
        """Retourne la liste des formats disponibles"""
        return list(self._strategies.keys())
    
    def is_registered(self, format_name: str) -> bool:
        """Vérifie que le modèle est enregistrée"""
        key = format_name.lower()

        if key in self._strategies:
            return True
        return False

    def unregister(self, format_name: str) -> None:
        """Supprime une stratégie enregistrée"""
        key = format_name.lower()

        if key in self._default_export:
            raise ValueError(f"Cannot unregister default model '{key}'")
        
        if key not in self._strategies:
            raise ValueError(f"Export type '{key}' is not registered")
        
        del self._strategies[key]
        logger.debug(f"Stratégie de fractionnement supprimée pour {key}")
    
    def export(
            self,
            format_name:str,
            results: Dict[str, Any],
            output_path: Path,
            **kwargs
    ) -> Path:
        """
        Exporte les résultats dans le format spécifié

        Args:
            format_name (str): Nom du format ('csv', 'json')
            results (Dict[str, Any]): Résultats de simulation
            output_path (Path): Chemin de sortie
            **kwargs: Options supplémentaires

        Returns:
            Path: Path du fichier créé
        """
        strategy = self._strategies.get(format_name.lower())

        if strategy is None:
            available = ', '.join(self.get_available_formats())
            raise ValueError(
                f"Format '{format_name}' non supporté. "
                f"Formats disponibles : {available}"
            )
        
        output_path.mkdir(parents=True, exist_ok=True)
        
        try:
            filepath = strategy.export(results, output_path, **kwargs)
            logger.info(f"Export {format_name} réussi : {filepath}")
            return filepath
        except Exception as e:
            logger.error(f"Erreur lors de l'export {format_name} : {e}")
            raise

    def export_all(
            self,
            results: Dict[str, Any],
            output_dir: Path,
            formats: Optional[list[str]] = None,
            **kwargs
    ) -> Dict[str, Path]:
        """
        Exporte dans plusieurs formats

        Args:
            results (Dict[str, Any]): Résultats de simulation
            output_dir (Path): Répertoire de sortie
            formats (list[str], optional): Liste des formats (ou tous si None). Defaults to None.
            **kwargs: Options supplémentaires

        Returns:
            Dict[str, Path]: Dict {format: filepath}
        """
        if formats is None:
            formats = self.get_available_formats()

        exported = {}

        for format_name in formats:
            try:
                filepath = self.export(format_name, results, output_dir, **kwargs)
                exported[format_name] = filepath
            except Exception as e:
                logger.warning(f"Impossible d'exporter en {format_name} : {e}")

        return exported