"""
Interface CLI interactive pour configurer et lancer des simulations

Usage directe :
    python -m interfaces.cli_interface

Permet de :
- Sélectionner les procédés à simuler
- Choisir l'ordre des procédés
- Configurer les paramètres de chaque procédé
- Définir les conditions initiales
- Sauvegarder la configuration
- Lancer la simulation
"""
import sys
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import json
from pathlib import Path

from .config_loader import ConfigLoader
