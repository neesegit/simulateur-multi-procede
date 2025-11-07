import plotly.graph_objects as go

from abc import ABC, abstractmethod
from typing import List, Dict
from datetime import datetime

class BasePlotter(ABC):
    """Classe de base pour tous les modules de tracé"""

    def __init__(self, fig: go.Figure, flows: List[Dict], timestamps: List[datetime], model_type: str, row: int, col: int) -> None:
        self.fig = fig
        self.flows = flows
        self.timestamps = timestamps
        self.model_type = model_type
        self.row = row
        self.col = col

    @abstractmethod
    def plot(self):
        pass

    def _add_trace(self, **kwargs) -> None:
        """Ajoute une courbe à la figure"""
        self.fig.add_trace(go.Scatter(**kwargs), row=self.row, col=self.col)