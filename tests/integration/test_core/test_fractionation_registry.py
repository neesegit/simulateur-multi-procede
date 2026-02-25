import pytest
from unittest.mock import MagicMock

class TestFractionationIntegration:
    """Tests d'intégration pour FractionationRegistry avec des fractionneurs réels"""

    def test_asm1_fractionation(self):
        """Test: Fractionnement ASM1"""
        from core.registries.fractionation.registry import FractionationRegistry

        registry = FractionationRegistry.get_instance()

        result = registry.fractionate(
            model_type='ASM1',
            cod=500.0,
            tss=200.0,
            tkn=40.0,
            nh4=25.0,
            no3=5.0,
            po4=8.0,
            alkalinity=200.0
        )

        expected_components = [
            'si', 'ss', 'xi', 'xs', 'so', 'snh', 'sno',
            'snd', 'xnd', 'xbh', 'xba', 'xp', 'salk'
        ]

        for component in expected_components:
            assert component in result
            assert isinstance(result[component], (int, float))
            assert result[component] >= 0
