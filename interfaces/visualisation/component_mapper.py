from typing import Dict, List

from core.model.model_registry import ModelRegistry

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

    def __init__(self) -> None:
        self.registry = ModelRegistry.get_instance()
        self.COMPONENT_LABELS: Dict[str, str] = {}
        self.COMPONENT_MAPPING: Dict[str, Dict[str, List[str]]] = {}
        model_types = self.registry.get_model_types()
        for model_type in model_types:
            model_def = self.registry.get_model_definition(model_type)
            comp = model_def.get_components_dict()
            self.COMPONENT_LABELS.update(comp)

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
    
    def get_label(self, component: str) -> str:
        """Retourne le label lisible d'un composant"""
        return self.COMPONENT_LABELS.get(component, component.lower())
    
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