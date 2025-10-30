"""
Méthodes de fractionnement pour convertir les paramètres mesurables (DCO, MES, NH4, etc) en composants des modèles ASM
"""
import logging

from typing import Dict, Optional

logger = logging.getLogger(__name__)

class ASM2dFraction:
    """
    Fractionnement des paramètres mesurables en composants ASM2d
    """

    DEFAULT_RATIOS = {
        # DCO
        'f_si_cod': 0.05,
        'f_sf_cod': 0.15, # DCO fermentescible (sucres)
        'f_sa_cod': 0.05, # DCO sous forme acétate (soluble biodégradable)
        'f_xs_cod': 0.40,
        'f_xi_cod': 0.10,
        'f_xh_cod': 0.20,
        'f_xpao_cod': 0.04, # Biomasse PAO
        'f_xaut_cod': 0.01, # Biomasse autotrophe

        # Azote
        'f_snh4_tkn': 0.70,
        'f_sno3_tn': 0.02, # Nitrates dans influent
        'i_n_si': 0.01, # Teneur N de SI
        'i_n_sf': 0.03, # Teneur N de SF
        'i_n_xs': 0.04, # Teneur N de XS

        # Phosphore total
        'f_spo4_tp': 0.60, # fraction soluble inorganique
        'f_xpp_xpao': 0.30, # Polyphosphates stockés
        'i_p_si': 0.00, # Teneur P de SI
        'i_p_sf': 0.01, # Teneur P de SF
        'i_p_xs': 0.01, # Teneur P de XI
        'i_p_bm': 0.02, # Teneur P biomasse

        # Biomasse
        'i_n_bm': 0.07, # Teneur N biomasse
        'i_n_xi': 0.02, # Teneur N inertes
        'i_tss_xi': 0.75, # TSS/COD pour XI
        'i_tss_xs': 0.75, # TSS/COD pour XS
        'i_tss_bm': 0.90, # TSS/COD pour biomasse

        # Alcalinité
        'alk_cod_ratio': 0.005 # Alcalinité / COD
    }

    @classmethod
    def fractionate(
        cls,
        cod: float,
        ss: float = 0.0,
        tkn: float = 0.0,
        nh4: float = 0.0,
        no3: float = 0.0,
        tp: float = 0.0,
        po4: float = 0.0,
        alkalinity: Optional[float] = None,
        cod_soluble: Optional[float] = None,
        rbcod: Optional[float] = None,
        vfa: Optional[float] = None,
        ratios: Optional[Dict[str, float]] = None
    ) -> Dict[str, float]:
        """
        Fractionne les paramètres mesurés en composants ASM2d

        Args:
            cod (float): DCO totale (mg/L)
            ss (float, optional): Solides en suspension (mg/L). Defaults to 0.0.
            tkn (float, optional): Azote Kjeldahl total (mg/L). Defaults to 0.0.
            nh4 (float, optional): Azote ammoniacal (mg/L). Defaults to 0.0.
            no3 (float, optional): Nitrates (mg/L). Defaults to 0.0.
            tp (float, optional): Phosphore total (mgP/L). Defaults to 0.0.
            po4 (float, optional): Phosphate inorganique (mgP/L). Defaults to 0.0.
            alkalinity (Optional[float], optional): Alcalinité (mmol/L). Defaults to None.
            cod_soluble (Optional[float], optional): DCO soluble (mg/L). Defaults to None.
            rbcod (Optional[float], optional): DCO rapidement biodégradable (mg/L). Defaults to None.
            vfa (Optional[float], optional): Acides gras volatils (mg COD/L). Defaults to None.
            ratios (Optional[Dict[str, float]], optional): Ratios personnalisés. Defaults to None.

        Returns:
            Dict[str, float]: Dictionnaire {nom composant: concentration (mg/L)}
        """
        r = {**cls.DEFAULT_RATIOS, **(ratios or {})}
        c = {}

        if cod_soluble is None:
            cod_soluble = cod * (r['f_si_cod'] + r['f_sf_cod'] + r['f_sa_cod'])
        cod_particulate = cod - cod_soluble

        # DCO soluble
        c['si'] = cod * r['f_si_cod']

        if rbcod is not None:
            c['sf'] = rbcod * 0.75
            c['sa'] = rbcod * 0.25
        elif vfa is not None:
            c['sa'] = vfa
            c['sf'] = cod * r['f_sf_cod']
        else:
            c['sf'] = cod * r['f_sf_cod']
            c['sa'] = cod * r['f_sa_cod']

        # DCO particulaire
        c['xi'] = cod * r['f_xi_cod']
        c['xs'] = cod * r['f_xs_cod']

        c['xh'] = cod * r['f_xh_cod']
        c['xpao'] = cod * r['f_xpao_cod']
        c['xaut'] = cod * r['f_xaut_cod']

        # Composés de stockage
        c['xpha'] = 0.0
        c['xpp'] = c['xpao'] * r['f_xpp_xpao']

        # autres biomasses mortes
        c['xmeoh'] = 0.0
        c['xmep'] = 0.0

        # Azote
        if tkn > 0:
            if nh4 > 0:
                c['snh4'] = nh4
            else:
                c['snh4'] = tkn * r['f_snh4_tkn']
            
            n_org = tkn - c['snh4']

            n_in_si = c['si'] * r['i_n_si']
            n_in_sf = c['sf'] * r['i_n_sf']
            n_in_xs = c['xs'] * r['i_n_xs']
            n_in_xi = c['xi'] * r['i_n_xi']
            n_in_biomass = (c['xh'] + c['xpao'] + c['xaut']) * r['i_n_bm']

            n_calculated = (n_in_si + n_in_sf + n_in_xs + n_in_xi + n_in_biomass)

            if n_calculated < n_org:
                logger.debug(f"Ajustement N organique : calculé={n_calculated:.1f}, mesuré={n_org:.1f}")
                deficit_n = n_org - n_calculated
                
                share_xs = 0.8
                share_xi = 0.2

                extra_cod_xs = (deficit_n * share_xs) / r['i_n_xs']
                extra_cod_xi = (deficit_n * share_xi) / r['i_n_xi']

                c['xs'] += extra_cod_xs
                c['xs'] += extra_cod_xi

                logger.debug(f"Ajustement N organique : ajouté à XS={extra_cod_xs:.2f} mgCOD/L, ajouté à XI={extra_cod_xi:.2f} mgCOD/L")
        else:
            c['snh4'] = nh4 if nh4 > 0 else 0.0

        c['sno3'] = no3

        c['sn2'] = 0.0

        # Phosphore
        if tp > 0:
            if po4 > 0:
                c['spo4'] = po4
            else:
                c['spo4'] = tp * r['f_spo4_tp']
            
            p_org = tp - c['spo4']

            p_in_si = c['si'] * r['i_p_si']
            p_in_sf = c['sf'] * r['i_p_sf']
            p_in_xs = c['xs'] * r['i_p_xs']
            p_in_xi = c['xi'] * r['i_p_xi']
            p_in_biomass = (c['xh'] + c['xpao'] + c['xaut']) * r['i_p_bm']

            p_calculated = (p_in_si + p_in_sf + p_in_xs + p_in_xi + p_in_biomass + c['xpp'])

            if p_calculated < p_org:
                c['xpp'] += (p_org - p_calculated)
                logger.debug(f"Ajustement XPP pour bilan P : {c['xpp']:.2f} mg P/L")
        else:
            c['spo4'] = po4 if po4 > 0 else 0.0

        # Oxygène dissous
        c['so2'] = 0.0

        if alkalinity is not None:
            c['salk'] = alkalinity
        else:
            c['salk'] = 5.0 + (cod * r['alk_cod_ratio'])

            if nh4 > 0:
                c['salk'] += nh4 * 0.7

        # TSS
        if ss > 0:
            c['xtss'] = ss
        else:
            tss_from_xi = c['xi'] * r['i_tss_xi']
            tss_from_xs = c['xs'] * r['i_tss_xs']
            tss_from_biomass = (c['xh'] + c['xpao'] + c['xaut']) * r['i_tss_bm']

            c['xtss'] = tss_from_xi + tss_from_xs + tss_from_biomass

        # Vérification bilan
        cod_calculated = sum(c[i] for i in ['si', 'sf', 'sa', 'xi', 'xs', 'xh', 'xpao', 'xaut', 'xpha'])

        if abs(cod_calculated - cod) > cod * 0.05:
            logger.warning(f"Biland DCO : mesuré={cod:.1f}, calculé={cod_calculated:.1f} mg/L")
            correction_factor = cod / cod_calculated
            c['xs'] += correction_factor
        
        for key, value in c.items():
            if value < 0:
                logger.warning(f"Composant {key} négatif ({value:.2f}), mis à zéro")
                c[key] = 0.0

        logger.debug(f"[ASM2dFraction] Fractionnement terminé : {len(c)} composants générés.")
        return c