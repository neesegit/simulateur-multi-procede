from typing import Dict, List

class ComponentMapper:
    """
    Mapper pour identifier les composants clés selon le modèle
    """

    COMPONENT_MAPPING = {
        'cod': {
            'ASM1': ['si', 'ss', 'xi', 'xs', 'xbh', 'xba', 'xp'],
            'ASM2D': ['si', 'sf', 'sa', 'xi', 'xs', 'xh', 'xpao', 'xaut', 'xpha']
        },
        'cod_soluble': {
            'ASM1': ['ss'],
            'ASM2D': ['sf', 'sa']
        },
        'cod_particulate': {
            'ASM1': ['xi', 'xs', 'xbh', 'xba', 'xp'],
            'ASM2D': ['xi', 'xs', 'xh', 'xpao', 'xaut']
        },
        'nitrogen': {
            'ASM1': ['snh', 'sno', 'snd', 'xnd'],
            'ASM2d': ['xi', 'xs', 'xh', 'xpao', 'xaut']
        },
        'nitrogen': {
            'ASM1': ['snh', 'sno', 'snd', 'xnd'],
            'ASM2D': ['snh4', 'sno3', 'sn2']
        },
        'nh4': {
            'ASM1': ['snh'],
            'ASM2D': ['snh4']
        },
        'no3': {
            'ASM1': ['sno'],
            'ASM2D': ['sno3']
        },
        'oxygen': {
            'ASM1': ['so'],
            'ASM2D': ['so2']
        },
        'biomass': {
            'ASM1': ['xbh', 'xba'],
            'ASM2D': ['xh', 'xpao', 'xaut']
        },
        'biomass_heterotrophs': {
            'ASM1': ['xbh'],
            'ASM2D': ['xh']
        },
        'biomass_autotrophs': {
            'ASM1': ['xba'],
            'ASM2D': ['xaut']
        },
        'biomass_pao': {
            'ASM1': [],
            'ASM2D': ['xpao']
        },
        'substrates': {
            'ASM1': ['ss', 'xs'],
            'ASM2D': ['sf', 'sa', 'xs']
        },
        'phosphorus': {
            'ASM1': [],
            'ASM2D': ['spo4', 'xpp']
        }
    }

    COMPONENT_LABELS = {
        'si': 'SI (inerte soluble)',
        'ss': 'SS (biodégradable rapide)',
        'xi': 'XI (inerte particulaire)',
        'xs': 'XS (biodégradable lent)',
        'xbh': 'XBH (hétérotrophes)',
        'xba': 'XBA (autotrophes)',
        'xp': 'XP (produits intertes)',
        'so': 'O2 dissous',
        'sno': 'NO3-',
        'snh': 'NH4+',
        'snd': 'N org. soluble',
        'xnd': 'N org. particulaire',
        'salk': 'Alcalinité',


        'so2': 'O2 dissous',
        'sf': 'SF (fermentescible)',
        'sa': 'SA (acétate)',
        'snh4': 'NH4+',
        'sno3': 'NO3-',
        'spo4': 'PO4 3-',
        'sn2': 'N2',
        'xh': 'XH (hétérotrophes)',
        'xpao': 'XPAO (PAO)',
        'xpp': 'XPP (polyphosphates)',
        'xpha': 'XPHA (PHA)',
        'xaut': 'XAUT (autotrophes)',
        'xtss': 'TSS',
        'xmeoh': 'XMEOH',
        'xmep': 'XMEP'
    }

    @classmethod
    def get_components(cls, category: str, model_type: str) -> List[str]:
        """
        Retourne les composants pour une catégorie et un modèle donnés

        Args:
            category (str): Catégorie de composants ('cod', 'nitrogent', etc)
            model_type (str): Type de modèle ('ASM1', 'ASM2D', etc)

        Returns:
            List[str]: Liste des noms de composants
        """
        model_type = model_type.upper().replace('MODEL', '')
        return cls.COMPONENT_MAPPING.get(category, {}).get(model_type, [])
    
    @classmethod
    def get_label(cls, component: str) -> str:
        """Retourne le label lisible d'un composant"""
        return cls.COMPONENT_LABELS.get(component, component.lower())
    
    @classmethod
    def extract_values(cls, flows: List[Dict], category: str, model_type: str) -> Dict[str, List[float]]:
        """
        Extrait les valeurs temporelles pour une catégorie de composants

        Args:
            flows (List[Dict]): Liste des flux temporels
            category (str): Catégorie de composants
            model_type (str): Type de modèle

        Returns:
            Dict[str, List[float]]: Dict {composant: [valeurs temporelles]}
        """
        components = cls.get_components(category, model_type)
        result = {}

        for comp in components:
            values = []
            for flow in flows:
                comp_dict = flow.get('components', {})
                values.append(comp_dict.get(comp, 0.0))
            result[comp] = values
        return result