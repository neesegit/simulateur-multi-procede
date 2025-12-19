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
        'f_si': 0.05,
        'f_xi': 0.10,
        'f_biomass': 0.08,
        'f_cv': 1.48,

        # Azote
        'f_snh': 0.70,
        'f_snd': 0.05
    }

    @classmethod
    def fractionate(
        cls,
        cod: float,
        cod_soluble: Optional[float] = None,
        tss: float = 0.0,
        tkn: float = 0.0,
        nh4: float = 0.0,
        no3: float = 0.0,
        po4: float = 0.0,
        alkalinity: Optional[float] = None,
        ratios: Optional[Dict[str, float]] = None
    ) -> Dict[str, float]:
        """
        Fractionne les paramètres mesurés en composants ASM1

        Args :
            cod : DCO totale (mg/L)
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
        if cod_soluble is not None:
            cod_soluble = max(0.0, min(cod_soluble, cod))
        else:
            cod_particulaire = min(cod, r['f_cv'] * tss)
            cod_soluble = max(0.0, cod - cod_particulaire)

        cod_particulaire = cod - cod_soluble

        components['si'] = r['f_si'] * cod
        components['ss'] = max(0.0, cod_soluble - components['si'])

        components['xi'] = r['f_xi'] * cod

        cod_biomass = r['f_biomass'] * cod
        components['xbh'] = 0.9 * cod_biomass
        components['xba'] = 0.1 * cod_biomass

        components['xs'] = max(
            0.0,
            cod_particulaire - components['xi'] - cod_biomass
        )

        components['xp'] = 0.0

        if tkn > 0:
            components['snh'] = nh4 if nh4 > 0 else r['f_snh'] * tkn
            components['snd'] = r['f_snd'] * tkn
            components['xnd'] = max(0.0, tkn - components['snh'] - components['snd'])
        else:
            components['snh'] = nh4
            components['snd'] = 0.0
            components['xnd'] = 0.0

        components['sno'] = no3

        # Oxygène dissous
        # Dans L'influent, généralement très faible
        components['so'] = 0.0

        # Alcalinité
        if alkalinity is not None:
            components['salk'] = alkalinity
        elif tkn > 0:
            components['salk'] = max(0.0, (tkn - no3) / 14.0)
        else:
            # typiquement 5-7 mmol/L pour eaux usées domestiques
            components['salk'] = 5.0

        cod_rebuilt = sum(components[c] for c in ['si', 'ss', 'xi', 'xs', 'xbh', 'xba', 'xp'])
        
        logger.debug(
            f"Fractionnement ASM1: DCO={cod:.1f} mg/L -> {len(components)} composants | "
            f"Rebuilt COD={cod_rebuilt:.1f} mg/L"
        )

        return components