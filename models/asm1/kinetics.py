import numpy as np

def calculate_process_rates(concentrations: np.ndarray, p: dict) -> np.ndarray:
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

        # Initialise le vecteur des vitesses
        rho = np.zeros(8)

        # Processus 1 : Croissance aérobie hétérotrophes
        # Limitation : substrat (SS), oxygène (SO)
        rho[0] = p['mu_h']*(ss/(p['k_s']+ss)) * (so/(p['k_oh']+so)) * xbh

        # Processus 2 : Croissance anoxie hétérotrophes (dénitrification)
        # Limitation : substrat (SS), nitrates (SNO), inhibition par oxygène
        rho[1] = p['mu_h'] * (ss / (p['k_s'] + ss)) * \
                 (p['k_oh'] / (p['k_oh'] + so)) * \
                 (sno / (p['k_no'] + sno)) * \
                 p['eta_g'] * xbh
        
        # Processus 3 : Croissance aérobie autotrophes (nitrification)
        # Limitation : ammonium (SNH), oxygène (SO)
        rho[2] = p['mu_a'] * (snh / (p['k_nh'] + snh)) * (so / (p['k_oa'] + so)) * xba

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
        xs_xbh_ratio = xs / (xbh + 1e-10) # Evite la division par zéro
        aerobic_factor = so / (p['k_oh'] + so)
        anoxic_factor = (p['k_oh'] / (p['k_oh'] + so)) * (sno / (p['k_no'] + sno))

        rho[6] = p['k_h'] * (xs_xbh_ratio / (p['k_x'] + xs_xbh_ratio)) * \
                 (aerobic_factor + p['eta_h'] * anoxic_factor) * xbh
        
        # Processus 8 : Hydrolyse azote organique
        # Proportionnel à l'hydrolyse des organiques
        rho[7] = rho[6] * (xnd / (xs + 1e-10))

        return rho