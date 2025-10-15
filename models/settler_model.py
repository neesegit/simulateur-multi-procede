"""
Modèle de décanteur secondaire (Settler) selon Takács et al. (1991)

Le décanteur sépare l'eau traitée des boues activées par sédimentation

Principe :
- Modèle 1D à couches empilées
- Flux de sédimentation (settling) vers le bas
- Flux de transport (advection) par le débit
- Compression des boues au fond
"""
from typing import Dict, Tuple, Optional, List
import numpy as np
from numpy.typing import NDArray
import logging

logger = logging.getLogger(__name__)

class SettlerModel:
    """Modèle de décanteur secondaire à couches (Takács)"""

    # Paramètres par défaut
    DEFAULT_PARAMS: Dict[str, float] = {
        'v0': 474.0, # Vitesse de sédimentation maximale (m/j)
        'rh': 5.76e-4, # Paramètre de sédimentation entravée (m^3/g)
        'rp': 2.86e-3, # Paramètre de sédimentation entravée (m^3/g)
        'fns': 2.28e-3, # Fraction non-settable
        'v0_max': 250.0, # Vitesse max pour solides non-settable (m/j)
    }

    def __init__(
            self,
            area: float,
            depth: float,
            n_layers: int = 10,
            params: Optional[Dict[str, float]] = None
    ) -> None:
        """
        Initialise le modèle de décanteur

        Args:
            area (float): Surface du décanteur (m²)
            depth (float): Profondeur totale (m)
            n_layers (int, optional): Nombre de couches pour la discrétisation. Defaults to 10.
            params (Optional[Dict[str, float]], optional): Paramètres du modèle. Utilise DEFAULT_PARAMS si None.
        """
        self.area: float = area
        self.depth: float = depth
        self.n_layers: int = n_layers

        # Paramètres du modèle
        self.params: Dict[str, float] = self.DEFAULT_PARAMS.copy()
        if params:
            self.params.update(params)

        # Géométrie des couches
        self.layer_height: float = depth / n_layers
        self.volument_per_layer: float = area * self.layer_height

        # Position de l'alimentation (typiquement au milieu)
        self.feed_layer: int = n_layers // 2

        # Concentrations dans chaque couche (mg/L)
        self.concentrations: NDArray[np.float64] = np.zeros(n_layers, dtype=np.float64)

        logger.info(
            f"SettlerModel initialisé: A={area}m², H={depth}m, "
            f"{n_layers} couches, feed layer={self.feed_layer}"
        )

    def initialize(
            self,
            initial_concentration: float = 3000.0
    ) -> None:
        """
        Initialise les concentrations dans toutes les couches

        Args:
            initial_concentration (float, optional): Concentration initiale uniforme (mg/L). Defaults to 3000.0.
        """
        self.concentrations.fill(initial_concentration)
        logger.debug(f"Concentrations initialisées à {initial_concentration} mg/L")

    def settling_velocity(
            self,
            concentration: float
    ) -> float:
        """
        Calcule la vitesse de sédimentation selon Takács

        Explication :
        La vitesse dépend de la concenrtation :
        - Faible concentration -> sédimentation rapide (particules libres)
        - Forte concentration -> sédimentation lente (entrave mutuelle)
        - Très forte concentration -> compression des boues

        Formule de Takács :
        vs = max(0, v0 x (e^(-rh x (X-fns x Xf)) - e^(-rp x (X-fns x Xf))))

        Args:
            concentration (float): Concentration de solides (mg/L = g/m^3)

        Returns:
            float: Vitesse de sédimentation (m/j)
        """
        v0: float = self.params['v0']
        rh: float = self.params['rh']
        rp: float = self.params['rp']
        fns: float = self.params['fns']

        # Conventration en g/m^3
        X: float = concentration

        # Concentration des non-settables
        Xf: float = X

        # Terme exponentiel
        exp_term: float = X - fns*Xf

        # Vitesse de sédimentation
        vs: float = max(
            0.0,
            v0 * (np.exp(-rh * exp_term) - np.exp(-rp * exp_term))
        )

        return vs
    
    def compute_fluxes(
            self,
            q_in: float,
            q_underflow: float
    ) -> Tuple[NDArray[np.float64], NDArray[np.float64]]:
        """
        Calcule les flux de transport et de sédimentation

        Args:
            q_in (float): Débit d'entrée (m^3/j)
            q_underflow (float): Débit de soutirage des boues (m^3/j)

        Returns:
            Tuple[NDArray[np.float64], NDArray[np.float64]] (flux_settling, flux transport):
                - flux_settling: Flux de sédimentation entre couches (kg/j)
                - flux_transport: Flux hydraulique entre couches (kg/j)
        """
        # Débit de surverse (clarified effluent)
        q_overflow: float = q_in-q_underflow

        # Flux de sédimentation (vers le bas)
        flux_settling: NDArray[np.float64] = np.zeros(self.n_layers + 1, dtype=np.float64)

        for i in range(self.n_layers):
            vs: float = self.settling_velocity(self.concentrations[i])
            # Flux = vitesse x surface x concentration (g/j)
            flux_settling[i + 1] = vs * self.area * self.concentrations[i]

        # Flux de transport hydraulique
        flux_transport: NDArray[np.float64] = np.zeros(self.n_layers + 1, dtype=np.float64)

        # Dans la partie supérieur (au-dessus du feed) : flux vers le haut
        for i in range(self.feed_layer):
            flux_transport[i] = (q_overflow/self.area) * self.concentrations[i]

        # Dans la partie inférieure (en-dessous du feed) : flux vers le bas
        for i in range(self.feed_layer, self.n_layers):
            flux_transport[i+1] = (q_underflow/self.area) * self.concentrations[i]

        return flux_settling, flux_transport
    
    def step(
            self,
            dt: float,
            q_in: float,
            x_in: float,
            q_underflow: float
    ) -> Tuple[float,float,float]:
        """
        Effectue un pas de temps de simulation

        Args:
            dt (float): Pas de temps (jours)
            q_in (float): Débit d'entrée (m^3/j)
            x_in (float): Concentration d'entrée (mg/L)
            q_underflow (float): Débit de soutirage (m^3/j)

        Returns:
            Tuple[float,float,float] (x_effluent, x_underflow, x_feed):
                - x_effluent: Concentration en sortie clarifiée (mg/L)
                - x_undeflow: Concentration des boues soutirées (mg/L)
                - x_feed: Concentration moyenne au point d'alimentation (mg/L) 
        """
        # Calcule les flux
        flux_settling, flux_transport = self.compute_fluxes(q_in, q_underflow)

        # Concentrations au prochain pas de temps
        c_next: NDArray[np.float64] = self.concentrations.copy()

        # Bilan de masse pour chaque couche
        for i in range(self.n_layers):
            # Flux net entrant dans la couche i
            flux_in: float = 0.0
            flux_out: float = 0.0

            # Flux de sédimentation
            if i > 0:
                flux_in += flux_settling[i] # De la couche supérieure
            if i < self.n_layers - 1:
                flux_out += flux_settling[i+1] # Vers la couche inférieure

            # Flux de transport
            if i == self.feed_layer:
                # Alimentation
                flux_in += q_in * x_in

            if i < self.feed_layer:
                # Transport ver le haut (overflow)
                flux_out += flux_transport[i]
                if i > 0:
                    flux_in += flux_transport[i-1]
            else:
                # Transport vers le bas (undeflow)
                if i < self.n_layers - 1:
                    flux_out += flux_transport[i+1]
                if i > 0:
                    flux_in += flux_transport[i]

            # Bilan : dC/dt = (flux_in - flux_out) / volume
            dc_dt: float = (flux_in - flux_out) / self.volument_per_layer

            # Mise à jour
            c_next[i] = max(0.0,self.concentrations[i] + dc_dt * dt)

        # Met à jour les concentrations
        self.concentrations = c_next

        # Concentrations de sortie
        x_effluent: float = float(self.concentrations[0]) # Surverse (top layer)
        x_underflow: float = float(self.concentrations[-1]) # Soutirage (bottom layer)
        x_feed: float = float(self.concentrations[self.feed_layer]) # feed layer

        return x_effluent, x_underflow, x_feed
    
    def get_concentration_profile(self) -> NDArray[np.float64]:
        """
        Retourne le profile de concentration vertical

        Returns:
            NDArray[np.float64]: Array des concentrations de haut en bas (mg/L)
        """
        return self.concentrations.copy()
    
    def get_sludge_blanket_height(
            self,
            threshold: float = 2000.0
    ) -> float:
        """
        Estime la hauteur du lit de boues

        Le lit de boues = zone où concentration > threshold

        Args:
            threshold (float, optional): Seuil de concentration (mg/L). Defaults to 2000.0.

        Returns:
            float: Hauteur du lit de boues (m)
        """
        # Trouve la couche la plus haute où C > threshold
        for i in range(self.n_layers):
            if self.concentrations[i] > threshold:
                # Hauteur = distance du fond
                height: float = (self.n_layers - i) * self.layer_height
                return height
            
        return 0.0 # Pas de lit de boues détecté
    
    def reset(self) -> None:
        """Réinitialise le décanteur"""
        self.concentrations.fill(0.0)
        logger.info("SettlerModel réinitialisé")

    def __repr__(self) -> str:
        avg_conc: float = float(np.mean(self.concentrations))
        return (
            f"<SettlerModel(area={self.area}m², depth={self.depth}m, )"
            f"layers={self.n_layers}, avg_conc={avg_conc:.1f}mg/L)>"
        )