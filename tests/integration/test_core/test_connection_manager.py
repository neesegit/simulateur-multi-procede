import pytest
from core.connection.connection_manager import ConnectionManager

class TestIntegrationWithConnectionManager:
    """Tests d'intégration avec ConnectionManager"""
    
    def test_visualize_ascii_method_exists(self):
        """Test : la méthode visualize_ascii existe"""
        cm = ConnectionManager()
        
        # Vérifier que la méthode peut être ajoutée
        assert hasattr(cm, 'visualize_ascii') or callable(getattr(cm, 'visualize_ascii', None))
    
    def test_all_styles_work_with_real_manager(self):
        """Test : tous les styles fonctionnent avec un vrai ConnectionManager"""
        cm = ConnectionManager()
        cm.add_connection('influent', 'proc1', 1.0, False)
        cm.add_connection('proc1', 'proc2', 0.6, False)
        cm.add_connection('proc1', 'proc3', 0.4, False)
        cm.add_connection('proc2', 'final', 1.0, False)
        cm.add_connection('proc3', 'final', 1.0, False)
        cm.add_connection('final', 'proc1', 0.3, True)
        
        from core.connection.connection_manager import ConnectionVisualizer
        visualizer = ConnectionVisualizer(cm)
        
        styles = ['simple', 'detailed', 'tree', 'flow']
        
        for style in styles:
            result = visualizer.visualize_ascii(style=style)
            
            assert isinstance(result, str)
            assert len(result) > 50
            assert 'proc1' in result