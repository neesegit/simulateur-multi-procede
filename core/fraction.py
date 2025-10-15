"""
Méthodes de fractionnement pour convertir les paramètres mesurables (DCO, MES, NH4, etc) en composants des modèles ASM
Basé sur les méthodologies standards :
- Henze et al. (2000) - Activated Sludge Models
- Roeleveld & Van Loosdrecht (2002)
"""
from typing import Dict, Optional
import logging

logger = logging.getLogger(__name__)

class ASM1Fraction:
    """
    Fractionnement des paramètres mesurables en composants ASM1
    """

    # Ratios par défaut (typiques pour eaux usées domestiques)
    DEFAULT_RATIOS = {
        # Fraction de la DCO
        'f_si_cod': 0.05, #DCO soluble inerte / DCO total
        'f_ss_cod': 0.20, #DCO soluble biodégradable / DCO total
        'f_xs_cod': 0.40, #DCO particulaire biodégradable / DCO total
        'f_xi_cod': 0.10, #DCO particulaire inerte / DCO total
        # Le reste (0.25) = biomasse dans l'influent

        # Fractions de l'azote
        'f_snh_tkn': 0.70, #NH4 / TKN
        'f_snd_tkn': 0.05, #Azote organique soluble / TKN
        'f_xnd_tkn': 0.25, #Azote organique particulaire / TKN

        # Ratios stoechimétriques
        'i_xb': 0.08, #Teneur en azote de la biomasse (gN/gDCO)
        'i_xp': 0.06, #Teneur en azote des produits inertes (gN/gDCO)

        # Fractions des MES
        'f_cv': 1.48, #Ratio DCO/MES typique pour particules organiques
    }

    @classmethod
    def fractionate(cls,
                    cod_total: float,
                    cod_soluble: Optional[float] = None,
                    ss: float = 0.0,
                    tkn: float = 0.0,
                    nh4: float = 0.0,
                    no3: float = 0.0,
                    po4: float = 0.0,
                    alkalinity: Optional[float] = None,
                    ratios: Optional[Dict[str, float]] = None) -> Dict[str, float]:
        """
        Fractionne les paramètres mesurés en composants ASM1

        Args :
            cod_total : DCO totale (mg/L)
            cod_soluble : DCO soluble (mg/L) - si None, estimée à 40% de la DCO totale
            ss : Solides en suspension (mg/L)
            tkn : Azote Kjeldahl total (mg/L)
            nh4 : Azote ammoniacal (mg/L)
            no3 : Nitrates (mg/L)
            po4 : Phosphates (mg/L)
            alkalinity : Alcalinité (mmol/L)
            ratios : Ratios personnalisés (remplace les valeurs par défauts)

        Returns : 
            Dictionnaire des composants ASM1 (mg/L)
        """
        # Utilise les ratios par défaut ou personnalisés
        r = {**cls.DEFAULT_RATIOS, **(ratios or {})}

        components = {}

        # Fractionnement de la DCO
        if cod_soluble is None:
            cod_soluble = cod_total * (r['f_si_cod'] + r['f_ss_cod'])

        cod_particulate = cod_total - cod_soluble

        # DCO soluble
        components['si'] = cod_total * r['f_si_cod'] # Inerte soluble
        components['ss'] = cod_total * r['f_ss_cod'] # Biodégradable soluble

        # DCO particulaire
        components['xi'] = cod_total * r['f_xi_cod'] # Inerte particulaire
        components['xs'] = cod_total * r['f_xs_cod'] # Biodégradable particulaire

        # Biomasse dans l'influent (estimation)
        cod_biomass = cod_total - (components['si'] + components['ss'] + components['xi'] + components['xs'])
        components['xbh'] = max(0, cod_biomass*0.9) # 90% hétérotrophes
        components['xba'] = max(0, cod_biomass*0.1) # 10% autotrophes

        # Produits inertes particulaires (initialement faible)
        components['xp'] = 0.0

        # Fractionnement de l'azote
        if tkn > 0:
            # Ammonium (mesuré ou estimé)
            if nh4 > 0:
                components['snh'] = nh4
            else:
                components['snh'] = tkn * r['f_snh_tkn']

            # Azote organique soluble
            components['snd'] = tkn * r['f_snd_tkn']

            # Azote organique particulaire
            n_organique_part = tkn - components['snh'] - components['snd']
            components['xnd'] = max(0, n_organique_part)
        else:
            components['snh'] = nh4 if nh4 > 0 else 0.0
            components['snd'] = 0.0
            components['xnd'] = 0.0

        # Nitrates
        components['sno'] = no3

        # Oxygène dissous
        # Dans L'influent, généralement très faible
        components['so'] = 0.0

        # Alcalinité
        if alkalinity is not None:
            components['salk'] = alkalinity
        else:
            # Estimation basée sur le TKN (corrélation empirique)
            # typiquement 5-7 mmol/L pour eaux usées domestiques
            components['salk'] = 5.0 + (tkn/14)*0.1 # conversion approximative
        
        logger.debug(f"Fractionnement ASM1: DCO={cod_total:.1f} -> {len(components)} composants")

        return components