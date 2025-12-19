"""
Méthodes de fractionnement pour verstir les paramètres mesurables en composants des modèles ASM
"""
import logging

from typing import Dict, Optional

logger = logging.getLogger(__name__)

class ASM3Fraction:
    """
    Fractionnement des paramètres mesurables en composants ASM3
    """

    DEFAULT_RATIOS = {
        'f_si_cod': 0.05,
        'f_ss_cod': 0.13,
        'f_xs_cod': 0.45,
        'f_xi_cod': 0.10,
        'f_xh_cod': 0.22,
        'f_xa_cod': 0.02,
        'f_xsto_cod': 0.03,

        'f_snh4_tkn': 0.70,
        'f_sno3_tn': 0.01, # Fraction no3 dans l'azote total
        'i_n_si': 0.01,
        'i_n_ss': 0.03,
        'i_n_xs': 0.04,
        'i_n_xi': 0.02,
        'i_n_bm': 0.07,

        'i_ss_xi': 0.75,
        'i_ss_xs': 0.75,
        'i_ss_bm': 0.90
    }

    @classmethod
    def fractionate(
        cls,
        cod: float,
        tss: float = 0.0,
        tkn: float = 0.0,
        nh4: float = 0.0,
        no3: float = 0.0,
        po4: float = 0.0,
        alkalinity: Optional[float] = None,
        cod_soluble: Optional[float] = None,
        rbcod: Optional[float] = None,
        ratios: Optional[Dict[str, float]] = None
    ) -> Dict[str, float]:
        """
        Fractionne les paramètres mesurés en composants ASM3

        Args:
            cod (float): DCO totale
            ss (float, optional): Solides en suspension. Defaults to 0.0.
            tkn (float, optional): Azote Kjeldahl total. Defaults to 0.0.
            nh4 (float, optional): Azote ammoniacal. Defaults to 0.0.
            no3 (float, optional): Nitrates. Defaults to 0.0.
            alkalinity (Optional[float], optional): Alcalinité. Defaults to None.
            cod_soluble (Optional[float], optional): DCO soluble. Defaults to None.
            rbcod (Optional[float], optional): DCO rapidement biodégradable. Defaults to None.
            ratios (Optional[Dict[str, float]], optional): Ratios personnalisés. Defaults to None.

        Returns:
            Dict[str, float]: Dictionnaire {nom composant: concentration}
        """
        r = {**cls.DEFAULT_RATIOS, **(ratios or {})}
        c = {}

        if cod_soluble is None:
            cod_soluble = cod * (r['f_si_cod'] + r['f_ss_cod'])

        c['si'] = cod * r['f_si_cod']

        if rbcod is not None:
            c['ss'] = rbcod
        else:
            c['ss'] = cod * r['f_ss_cod']

        c['xs'] = cod * r['f_xs_cod']
        c['xi'] = cod * r['f_xi_cod']

        c['xh'] = cod * r['f_xh_cod']
        c['xa'] = cod * r['f_xa_cod']
        c['xsto'] = cod * r['f_xsto_cod']

        if tkn > 0:
            if nh4 > 0:
                c['snh4'] = nh4
            else:
                c['snh4'] = tkn * r['f_snh4_tkn']

            n_org = tkn - c['snh4']

            n_in_si = c['si'] * r['i_n_si']
            n_in_ss = c['ss'] * r['i_n_ss']
            n_in_xs = c['xs'] * r['i_n_xs']
            n_in_xi = c['xi'] * r['i_n_xi']
            n_in_biomass = (c['xh'] + c['xa']) * r['i_n_bm']

            n_calculated = n_in_si + n_in_ss + n_in_xs + n_in_xi + n_in_biomass

            if n_calculated < n_org:
                logger.debug(f'Ajustement N organique : calculé={n_calculated:.1f}, mesuré={n_org:.1f}')
                deficit_n = n_org - n_calculated

                share_xs = 0.8
                share_xi = 0.2

                extra_cod_xs = (deficit_n*share_xs) / r['i_n_xs']
                extra_cod_xi = (deficit_n*share_xi) / r['i_n_xi']

                c['xs'] += extra_cod_xs
                c['xi'] += extra_cod_xi

                logger.debug(f"Azote : +{extra_cod_xs:.2f} mgCOD/L à XS, +{extra_cod_xi:.2f} mgCOD/L à XI")
        else:
            c['snh4'] = nh4 if nh4 > 0 else 0.0

        c['snox'] = no3

        c['sn2'] = 0.0

        c['so2'] = 0.0

        if alkalinity is not None:
            c['salk'] = alkalinity
        elif tkn > 0:
            c['salk'] = max(0.0, (tkn - no3) / 14.0)
        else:
            c['salk'] = 5.0
        
        if tss > 0:
            c['xss'] = tss
        else:
            tss_from_xi = c['xi'] * r['i_ss_xi']
            tss_from_xs = c['xs'] * r['i_ss_xs']
            tss_from_biomass = (c['xh'] + c['xa']) * r['i_ss_bm']
            tss_from_xsto = c['xsto'] * 0.60

            c['xss'] = tss_from_xi + tss_from_xs + tss_from_biomass + tss_from_xsto

        cod_calculated = sum(c[comp] for comp in ['si', 'ss', 'xi', 'xs', 'xh', 'xa', 'xsto'])

        if abs(cod_calculated - cod) > cod * 0.05:
            logger.warning(f"Bilan DCO : mesuré={cod:.1f}, calculé={cod_calculated:.1f} mg/L")

            correction = cod - cod_calculated
            c['xs'] += correction
            logger.debug(f"Correction DCO appliquée sur XS : {correction:.2f} mg/L")

        for key, value in c.items():
            if value < 0:
                logger.warning(f"Composant {key} négatif ({value:.2f}), mis à zéro")
                c[key] = 0.0

        logger.debug(f"[ASM3Fraction] Fractionnement terminé : {len(c)} composants générés.")

        return c