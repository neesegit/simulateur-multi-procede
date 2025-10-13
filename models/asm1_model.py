"""
Implémentation du modèle ASM1 (Activated Sludge Model 1)
Basé sur Henze et al. (2000)

Le modèle comprend :
- 13 composants (SI, SS, XI, XS, XBH, XBA, XP, SO, SNO, SNH, SND, XND, SALK)
- 8 processus biologiques
"""
import numpy as np
from typing import Dict, Optional
import logging

logger = logging.getLogger(__name__)

class ASM1Model:
    """
    Modèle ASM1 pour la simulation des boues activées
    """

    # Indices des composants dans le vecteur de concentration
    COMPONENT_INDICES = {
        'si': 0, # Substrat inerte soluble (mg COD/L)
        'ss': 1, # Substrat rapidement biodégradable (mg COD/L)
        'xi': 2, # Substrat inerte particulaire (mg COD/L)
        'xs': 3, # substrat inerte particulaire (mg COD/L)
        'xbh': 4, # Biomasse hétérotrophe active (mg COD/L)
        'xba': 5, # Biomasse autotrophe active (mg COD/L)
        'xp': 6, # Produits inertes particulaires (mg COD/L)
        'so': 7, # Oxygène dissosu (mg O2/L)
        'sno': 8, # Nitrates et nitrites (mg N/L)
        'snh': 9, # Ammonium (mg N/L)
        'snd': 10, # Azote organique soluble (mg/L)
        'xnd': 11, # Azote organique particulaire (mg/L)
        'salk': 12 # Alcalinité (mmol/L)
    }

    # Paramètres par défaut (valeurs typiques à 20°C)
    DEFAULT_PARAMS = {
        # Paramètres cinétiques hétérotrophes
        'mu_h': 6.0, # Taux de croissance max hétérotrophes (1/j)
        'k_s': 20.0, # constante de demi_saturation substrat (mg COD/L)
        'k_oh': 0.2, # Constante de demi-saturation O2 hétérotrophes (mg O2/L)
        'k_no': 0.5, # Constante de demi-saturation nitrates (mg N/L)
        'b_h': 0.62, # Taux de décès hétérotrophes (1/j)

        # Paramètres cinétiques autotrophes
        'mu_a': 0.8, # Taux de croissance max autotrophes (1/j)
        'k_nh': 1.0, # Constante de demi-saturation ammonium (mg N/L)
        'k_oa': 0.4, # Constante de demi-saturation O2 autotrophes (mg O2/L)
        'b_a': 0.2, # Taux de décès autotrophes (1/j)

        # Facteurs de correction
        'eta_g': 0.8, # Facteur de correction pour croissance anoxie
        'eta_h': 0.4, # Facteur de correction pour hydrolise anoxie

        # Paramètres d'hydrolyse
        'k_h': 3.0, # Taux d'hydrolyse max (1/j)
        'k_x': 0.03, # Constante de demi-saturation pour hydrolyse

        # Paramètres d'ammonification
        'k_a': 0.08, # Taux d'ammonification (L/mg COD/j)

        # Paramètres stoechiométriques
        'y_h': 0.67, # Rendement hétérotrophes
        'y_a': 0.24, # Redement autotrophes
        'f_p': 0.08, # Fraction de biomasse donnant produits inertes
        'i_xb': 0.08, # Teneur en N de la biomasse (mg N/mg COD)
        'i_xp': 0.06, # Teneur en N des produits inertes (mg N/mg COD)
    }

    def __init__(self, params: Optional[Dict[str, float]] = None):
        """
        Initialise le modèle ASM1

        Args:
            params (Dict[str, float], optional): Dictionnaire de paramètres. Utilise DEFAULT_PARAMS si None
        """

        # Utilise les paramètres par défaut et override avec ceux fournis
        self.params = self.DEFAULT_PARAMS.copy()
        if params:
            self.params.update(params)

        # Construit la matrice stoechiométrique (8 processus x 13 composants)
        self.stoichiometric_matrix = self._build_stoichiometric_matrix()
    
    def _build_stoichiometric_matrix(self) -> np.ndarray:
        """
        Construit la matrice stoechiométrique S (8x13)
        
        Cahque ligne = un processus biologique
        Chaque colonne = un composant
        Valeur = coefficient stoechiométique

        Returns:
            np.ndarray: Matrice numpy 8x13
        """
        S = np.zeros((8,13))

        # Paramètres stoechiométriques
        y_h = self.params['y_h']
        y_a = self.params['y_a']
        f_p = self.params['f_p']
        i_xb = self.params['i_xb']
        i_xp = self.params['i_xp']

        # Processus 1 : Croissance aérobie des hétérotrophes
        ## SS + O2 + NH4 -> XBH
        S[0,1] = -1/y_h                 # SS consommé
        S[0,4] = 1                      # XBH produit
        S[0,7] = -(1-y_h)/y_h           # O2 consommé
        S[0,9] = -i_xb                  # NH4 consommé
        S[0,12] = -i_xb / 14            # Alcalinité consommé

        # Processus 2 : Croissance anoxie des hétérotrophes (dénitrification)
        # SS + NO3 + NH4 -> XBH + N2
        S[1,1] = -1/y_h                                 # SS consommé
        S[1,4] = 1                                      # XBH produit
        S[1,8] = -(1-y_h) / (2.86*y_h)                  # NO3 consommé (2.86 = ratio DCO/N)
        S[1,9] = -i_xb                                  # NH4 consommé
        S[1,12] = ((1-y_h) / (14*2.86*y_h)) - (i_xb/14) # alcalinité produite

        # Processus 3 : Croissance aérobie des autotrophes (nitrification)
        # NH4 + O2 -> XBA + NO3
        S[2,5] = 1                          # XBA produit
        S[2,7] = -(4.57 - y_a) / y_a        # O2 consommé (4.57 g O2/g N)
        S[2,8] = 1/y_a                      # NO3 produit
        S[2,9] = -i_xb - (1/y_a)            # NH4 consommé
        S[2,12] = -(i_xb/14) - (1/(7*y_a))  # Alcalinité consommé

        # Processus 4 : Décès des hétérotrophes
        # XBH -> XS + XP + XND
        S[3,3] = 1 - f_p            # XS produit
        S[3,4] = -1                 # XBH consommé
        S[3,6] = f_p                # XP produit
        S[3,11] = i_xb - f_p*i_xp   # XND produit

        # Processus 5 : Décès des autotrophes
        # XBA -> XS + XP + XND
        S[4,3] = 1 - f_p                # XS produit
        S[4,5] = -1                     # XBA consommé
        S[4,6] = f_p                    # XP produit
        S[4,11] = i_xb - f_p * i_xp     # XND produit

        # Processus 6 : Ammonification (minéralisation azote organique soluble)
        # SND -> SNH
        S[5,9] = 1      # SNH produit
        S[5,10] = -1    # SND consommé
        S[5,12] = 1/14  # Alcalinité produite

        # Processus 7 : Hydrolyse des organiques particulaires
        # XS -> SS
        S[6,1] = 1      # SS produit
        S[6,3] = -1     # XS consommé

        # Processus 8 : Hydrolyse de l'azote organique particulaire
        # XND -> SND
        S[7,10] = 1     # SND produit
        S[7,11] = -1    # XND consommé

        return S
    
    def calculate_process_rates(self, concentrations: np.ndarray) -> np.ndarray:
        """
        Calcule les vitesses des 8 processus biologiques (vecteur Rho)

        Explication :
        Chaque processus a une cinétique de type Monod :
        Rho = mu_max x (S/ (Ks + S)) x (O2 / (KO + O2)) x Biomasse

        où :
        - mu_max = vitesse maximale
        - S / (Ks + S) = limitation par le substrat (terme de Monod)
        - O2 / (KO + O2) = limitation par l'oxygène
        - Biomasse = concentration de micro-organismes

        Args:
            concentrations (np.ndarray): Vecteur des 13 concentrations (mg/L)

        Returns:
            np.ndarray: Vecteur des 8 vitesses de processus (mg/L/j)
        """

        # Extrait les concentrations
        ss = concentrations[1] # Substrat rapidement biodégradable
        xs = concentrations[3] # Substrat lentement biodégradable
        xbh = concentrations[4] # Biomasse hétérotrophe
        xba = concentrations[5] # Biomasse autotrophe
        so = concentrations[7] # Oxygène dissous
        sno = concentrations[8] # Nitrates
        snh = concentrations[9] # Ammonium
        snd = concentrations[10] # Azote organique soluble
        xnd = concentrations[11] # Azote organique particulaire

        # Paramètres cinétiques
        p = self.params # raccourci

        # Initialise le vecteur des vitesses
        rho = np.zeros(8)

        # Processus 1 : Croissance aérobie hétérotrophes
        # Limitation : substrat (SS), oxygène (SO)
        rho[0] = p['mu_h']*(ss/(p['k_s']+ss)) * (so/(p['k_oh']+so)) * xbh

        # Processus 2 : Croissance anoxie hétérotrophes (dénitrification)
        # Limitation : substrat (SS), nitrates (SNO), inhibition par oxygène
        rho[1] = p['mu_h'] * (ss / (p['k_s']+ss)) * \
                 (p['k_oh'] / (p['k_oh']+so)) * \
                 (sno / (p['k_no'] + sno)) * \
                 p['eta_g'] * xbh
        
        # Processus 3 : Croissance aérobie autotrophes (nitrification)
        # Limitation : ammonium (SNH), oxygène (SO)
        rho[2] = p['mu_a'] * (snh / (p['k_nh']+snh)) * (so / (p['k_oa'] + so)) * xba

        # Processus 4 : Décès hétérotrophes
        # Proportionnel à la biomasse
        rho[3] = p['b_h'] * xbh

        # Processus 5 : Décès autotrophes
        rho[4] = p['b_a'] * xba

        # Processus 6 : Ammonification
        # Proportionnel à SND et XBH
        rho[5] = p['k_a'] * snd * xbh

        # Processus 7 : Hydrolyse des organiques
        # Limitation : rapport XS/XBH, conditions aérobies/anoxiques
        xs_xbh_ratio = xs / (xbh+1e-10) # Evite la division par zéro
        aerobic_factor = so / (p['k_oh'] + so)
        anoxic_factor = (p['k_oh'] / (p['k_oh'] + so)) * (sno / (p['k_no'] + sno))

        rho[6] = p['k_h'] * (xs_xbh_ratio / (p['k_x'] + xs_xbh_ratio)) * \
                 (aerobic_factor + p['eta_h'] * anoxic_factor) * xbh
        
        # Processus 8 : Hydrolyse azote organique
        # Proportionnel à l'hydrolyse des organiques
        rho[7] = rho[6] * (xnd / (xs+1e-10))

        return rho
    
    def compute_derivatives(self, concentrations: np.ndarray) -> np.ndarray:
        """
        Calcule les dérivées dC/dt pour les 13 composants

        Explication :
        dC/dt = sum(vitesse_processus x coefficient_stoechiométrique)
        En algèbre matricielle : dC/dt = S^T x Rho

        Args:
            concentrations (np.ndarray): Vecteur des concentrations actuelles (13,)

        Returns:
            np.ndarray: Vecteur des dérivées dC/dt (13,)
        """
        # Calcule les vitesses des processus
        rho = self.calculate_process_rates(concentrations)

        # Multiplie par la matrice stoechiométrique transposée
        # S^T : 13x8, Rho : 8x1 -> résultat : 13x1
        derivatives = self.stoichiometric_matrix.T @ rho

        return derivatives
    
    def step(self, concentrations: np.ndarray, dt: float, so_setpoint: Optional[float] = None) -> np.ndarray:
        """
        Effectue un pas de temps de simulation avec méthode d'Euler

        Explication :
        Méthode d'Euler explicite : C(t+dt) = C(t) + dC/dt x dt

        C'est la méthode la plus simple pour résoudre une EDO
        Plus dt est petit, plus c'est précis

        Args:
            concentrations (np.ndarray): Concentrations au temps t (13,)
            dt (float): Pas de temps (jours)
            so_setpoint (float, optional): Consigne d'oxygène dissous(mg/L) - si fournie, SO est fixé

        Returns:
            np.ndarray: Concentrations au temps t+dt (13,)
        """
        # Calcule les dérivées
        derivatives = self.compute_derivatives(concentrations)

        # Méthode d'Euler : C_next = C_current + dC/dt x dt
        concentration_next = concentrations + derivatives*dt

        # Contraintes : concentration >= 0 (pas de valeurs négatives)
        concentrations_next = np.maximum(concentration_next, 1e-10)

        # Si consigne d'oxygène fournie, on la fixe (contrôle d'aération)
        if so_setpoint is not None:
            concentrations_next[7] = so_setpoint

        return concentrations_next
    
    def get_component_names(self) -> list:
        """
        Retourne les noms des 13 composants dans l'odre

        Returns:
            list
        """
        return list(self.COMPONENT_INDICES.keys())
    
    def concentrations_to_dict(self, concentrations: np.ndarray) -> Dict[str, float]:
        """
        Convertit un vecteur de concentrations en dictionnaire

        Args:
            concentrations (np.ndarray): Vecteur numpy (13,)

        Returns:
            Dict[str, float]: Dictionnaire {nom_composant: valeur}
        """
        return {name: concentrations[idx] for name, idx in self.COMPONENT_INDICES.items()}
    
    def dict_to_concentrations(self, conc_dict: Dict[str, float]) -> np.ndarray:
        """
        convertit un dictionnaire de concentrations en vecteur numpy

        Args:
            conc_dict (Dict[str, float]): dictionnaire {nom_composant: valeur}

        Returns:
            np.ndarray: Vecteur numpy(13,)
        """
        concentrations = np.zeros(13)
        for name, value in conc_dict.items():
            if name in self.COMPONENT_INDICES:
                concentrations[self.COMPONENT_INDICES[name]] = value
        return concentrations

        