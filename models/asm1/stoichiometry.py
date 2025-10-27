import numpy as np

def build_stoichiometric_matrix(params: dict) -> np.ndarray:
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
        y_h = params['y_h']
        y_a = params['y_a']
        f_p = params['f_p']
        i_xb = params['i_xb']
        i_xp = params['i_xp']

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