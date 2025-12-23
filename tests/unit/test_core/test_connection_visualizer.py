"""
Tests unitaires pour la visualisation ASCII du connectionmanager
"""
import pytest
from unittest.mock import Mock, MagicMock, patch

from core.connection.connection_manager import ConnectionManager
from core.connection.connection import Connection
from core.connection.connection_visualizer import ConnectionVisualizer

class TestConnectionVisualizerBasics:
    """Tests de base pour le visualiseur"""

    def test_visualizer_initialization(self):
        """Test : création du visualiseur"""
        manager = ConnectionManager()
        visualizer = ConnectionVisualizer(manager)

        assert visualizer is not None
        assert visualizer.manager is manager

    def test_visualize_ascii_returns_string(self):
        """Test : visualize_ascii retourne une chaîne"""
        cm = ConnectionManager()
        cm.add_connection('s', 't', 1.0, False)

        visualizer = ConnectionVisualizer(cm)

        result = visualizer.visualize_ascii()

        assert isinstance(result, str)

        assert len(result) > 0

    def test_empty_graph_visualization(self):
        """Test : visualisation d'un graphe vide"""
        cm = ConnectionManager()

        visualizer = ConnectionVisualizer(cm)

        result = visualizer.visualize_ascii(style='simple')

        assert isinstance(result, str)
        assert "GRAPHE" in result or "connexions" in result.lower()

class TestSimpleVisualization:
    """Tests pour le style 'simple'"""

    def test_simple_style_basic(self):
        """Test : style simple basique"""
        cm = ConnectionManager()
        cm.add_connection('s', 't', 1.0, False)

        visualizer = ConnectionVisualizer(cm)

        result = visualizer.visualize_ascii(style='simple')

        assert 's' in result
        assert 't' in result
        assert '->' in result

    def test_simple_shows_fractions(self):
        """Test : affiche les fractions"""
        cm = ConnectionManager()
        cm.add_connection('s', 't', 0.5, False)

        visualizer = ConnectionVisualizer(cm)

        result = visualizer.visualize_ascii(style='simple')

        assert '50%' in result or '0.5' in result

    def test_simple_marks_recycling(self):
        """Test : marque les recyclages"""
        cm = ConnectionManager()
        cm.add_connection('s', 't', 1.0, True)

        visualizer = ConnectionVisualizer(cm)

        result = visualizer.visualize_ascii(style='simple')

        assert 'recyclage' in result.lower() or '[R]' in result

    def test_simple_shows_sinks(self):
        """Test : affiche les noeuds puits"""
        cm = ConnectionManager()
        cm.add_connection('s', 'm', 1.0, False)
        cm.add_connection('m', 'sink', 1.0, False)

        visualizer = ConnectionVisualizer(cm)

        result = visualizer.visualize_ascii(style='simple')

        assert 'sink' in result

class TestDetailedVisualization:
    """Tests pour le style 'detailed'"""

    def test_detailed_shows_statistics(self):
        """Test : affiche les statistiques"""
        cm = ConnectionManager()
        cm.add_connection('s', 't', 1.0, False)

        visualizer = ConnectionVisualizer(cm)

        result = visualizer.visualize_ascii(style='detailed', show_stats=True)
        
        assert 'STATISTIQUES' in result
        assert 'noeuds' in result or 'Noeuds' in result
        assert 'Connexions' in result or 'connexions' in result

    def test_detailed_without_statistics(self):
        """Test : peut masquer les statistiques"""
        cm = ConnectionManager()
        cm.add_connection('s', 't', 1.0, False)

        visualizer = ConnectionVisualizer(cm)

        result_with = visualizer.visualize_ascii(style='detailed', show_stats=True)
        result_without = visualizer.visualize_ascii(style='detailed', show_stats=False)

        assert 'STATISTIQUES' in result_with
        assert len(result_without) < len(result_with)

    def test_detailed_highlights_cycles(self):
        """Test : met en évidence les cycles"""
        cm = ConnectionManager()
        cm.add_connection('n1', 'n2', 1.0, False)
        cm.add_connection('n2', 'n3', 1.0, False)
        cm.add_connection('n3', 'n1', 1.0, True)

        visualizer = ConnectionVisualizer(cm)

        result = visualizer.visualize_ascii(style='detailed', highlight_cycles=True)

        assert 'CYCLES' in result or 'cycle' in result.lower()

    def test_detailed_shows_sources(self):
        """Test : identifie les sources"""
        cm = ConnectionManager()
        cm.add_connection('influent', 'p1', 1.0, False)
        cm.add_connection('p1', 'p2', 1.0, False)

        visualizer = ConnectionVisualizer(cm)

        result = visualizer.visualize_ascii(style='detailed')

        assert 'SOURCES' in result or 'sources' in result
        assert 'influent' in result

    def test_detailed_shows_sinks(self):
        """Test : identifie les puits"""
        cm = ConnectionManager()
        cm.add_connection('p1', 'p2', 1.0, False)
        cm.add_connection('p2', 'final', 1.0, False)

        visualizer = ConnectionVisualizer(cm)

        result = visualizer.visualize_ascii(style='detailed')

        assert 'PUITS' in result or 'puits' in result
        assert 'final' in result

    def test_detailed_shows_upstream_downstream(self):
        """Test : affiche entrées et sorties pour chaque noeud"""
        cm = ConnectionManager()
        cm.add_connection('s', 'm', 1.0, False)
        cm.add_connection('m', 't', 1.0, False)

        visualizer = ConnectionVisualizer(cm)

        result = visualizer.visualize_ascii(style='detailed')

        assert 'Entrées' in result
        assert 'Sorties' in result

    def test_detailed_calculates_totals(self):
        """Test : calcule les totaux entrant/sortant"""
        cm = ConnectionManager()
        cm.add_connection('s', 't1', 0.6, False)
        cm.add_connection('s', 't2', 0.4, False)

        visualizer = ConnectionVisualizer(cm)

        result = visualizer.visualize_ascii(style='detailed')

        assert 'Total' in result or 'total' in result
        assert '100' in result

class TestTreeVisualization:
    """tests pour le style 'tree'"""

    def test_tree_style_basic(self):
        """Test : style arbre basique"""
        cm = ConnectionManager()
        cm.add_connection('root', 'child1', 1.0, False)
        cm.add_connection('root', 'child2', 1.0, False)

        visualizer = ConnectionVisualizer(cm)

        result = visualizer.visualize_ascii(style='tree')

        assert 'root' in result
        assert 'child1' in result
        assert 'child2' in result
        assert '└──' in result or '├──' in result or '│' in result

    def test_tree_hierarchical_structure(self):
        """Test : structure hiérarchique correcte"""
        cm = ConnectionManager()
        cm.add_connection('level0', 'level1', 1.0, False)
        cm.add_connection('level1', 'level2', 1.0, False)

        visualizer = ConnectionVisualizer(cm)

        result = visualizer.visualize_ascii(style='tree')

        lines = result.split('\n')
        level0_line = next((i for i, line in enumerate(lines) if 'level0' in line), None)
        level1_line = next((i for i, line in enumerate(lines) if 'level1' in line), None)
        level2_line = next((i for i, line in enumerate(lines) if 'level2' in line), None)

        if level0_line is not None and level1_line is not None and level2_line is not None:
            assert level0_line < level1_line < level2_line

    def test_tree_detects_visited_nodes(self):
        """Test : détecte les noeuds déjà visités (cycles)"""
        cm = ConnectionManager()
        cm.add_connection('n1', 'n2', 1.0, False)
        cm.add_connection('n2', 'n3', 1.0, False)
        cm.add_connection('n3', 'n1', 1.0, True)

        visualiser = ConnectionVisualizer(cm)

        result = visualiser.visualize_ascii(style='tree')

        assert 'visité' in result.lower()

    def test_tree_shows_fractions_optional(self):
        """Test : peut afficher ou masquer les fractions"""
        cm = ConnectionManager()
        cm.add_connection('s', 't', 0.5, False)

        visualiser = ConnectionVisualizer(cm)

        result_with = visualiser.visualize_ascii(style='tree', show_fractions=True)
        result_without = visualiser.visualize_ascii(style='tree', show_fractions=False)

        assert '50%' in result_with or '0.5' in result_with
        assert '50%' not in result_without or '0.5' not in result_without

    def test_tree_handles_no_sources(self):
        """Test : gère l'absence de sources (graphes cyclique)"""
        cm = ConnectionManager()
        cm.add_connection('n1', 'n2', 1.0, False)
        cm.add_connection('n2', 'n1', 1.0, False)

        visualiser = ConnectionVisualizer(cm)

        result = visualiser.visualize_ascii(style='tree')

        assert 'source' in result.lower() or 'cyclique' in result.lower()

class TestFlowvisualization:
    """Tests pour le style 'flow'"""

    def test_flow_style_basic(self):
        """test : style flux basique"""
        cm = ConnectionManager()
        cm.add_connection('influent', 'p1', 1.0, False)
        cm.add_connection('p1', 'p2', 1.0, False)

        visualizer = ConnectionVisualizer(cm)

        result = visualizer.visualize_ascii(style='flow')

        assert 'influent' in result
        assert 'p1' in result
        assert 'p2' in result
        assert '│' in result or '▼' in result

    def test_flow_shows_sequential_order(self):
        """Test : respect l'ordre d'exécution"""
        cm = ConnectionManager()
        cm.add_connection('influent', 'f', 1.0, False)
        cm.add_connection('f', 's', 1.0, False)
        cm.add_connection('s', 't', 1.0, False)

        visualizer = ConnectionVisualizer(cm)

        result = visualizer.visualize_ascii(style='flow')

        lines = result.split('\n')
        first_line = next((i for i, line in enumerate(lines) if 'f' in line), None)
        second_line = next((i for i, line in enumerate(lines) if 's' in line), None)
        third_line = next((i for i, line in enumerate(lines) if 't' in line), None)

        if first_line is not None and second_line is not None and third_line is not None:
            assert first_line < second_line < third_line

    def test_flow_marks_recycling_seprately(self):
        """test : marque les recyclages sur le côté"""
        cm = ConnectionManager()
        cm.add_connection('p1', 'p2', 1.0, False)
        cm.add_connection('p2', 'p1', 0.5, True)

        visualizer = ConnectionVisualizer(cm)

        result = visualizer.visualize_ascii(style='flow')

        assert '[R]' in result or 'recyclage' in result.lower()

    def test_flow_shows_end_marker(self):
        """Test : marque la fin du flux"""
        cm = ConnectionManager()
        cm.add_connection('s', 't', 1.0, False)

        visualizer = ConnectionVisualizer(cm)

        result = visualizer.visualize_ascii(style='flow')

        assert 'FIN' in result or 'fin' in result

    def test_flow_handles_cyclic_graph(self):
        """Test : gère les graphes cycliques"""
        cm = ConnectionManager()
        cm.add_connection('n1', 'n2', 1.0, False)
        cm.add_connection('n2', 'n1', 1.0, False)

        visualizer = ConnectionVisualizer(cm)

        result = visualizer.visualize_ascii(style='flow')

        assert 'Impossible' in result or 'erreur' in result.lower()

class TestVisualizerOption:
    """Tests des options de visualisation"""

    def test_invalid_style_defaults_to_detailed(self):
        """Test : style invalide utilise 'detailed' par défaut"""
        cm = ConnectionManager()
        cm.add_connection('s', 't', 1.0, False)

        visualizer = ConnectionVisualizer(cm)

        result = visualizer.visualize_ascii(style='invalid_style')

        assert isinstance(result, str)
        assert len(result) > 0

    def test_show_fractions_true(self):
        """Test : show_fraction=True affiche les fractions"""
        cm = ConnectionManager()
        cm.add_connection('s', 't', 0.7, False)

        visualizer = ConnectionVisualizer(cm)

        result = visualizer.visualize_ascii(show_fractions=True)

        assert '70' in result or '0.7' in result

    def test_show_fractions_false(self):
        """Test : show_fractions=False masque les fractions"""
        cm = ConnectionManager()
        cm.add_connection('s', 't', 0.7, False)

        visualizer = ConnectionVisualizer(cm)

        result = visualizer.visualize_ascii(show_fractions=False)

        assert 's' in result
        assert 't' in result

class TestHelperMethods:
    """Tests des méthodes auxiliaires"""

    def test_get_source_nodes(self):
        """Test : identifie correctement les sources"""
        cm = ConnectionManager()
        cm.add_connection('s1', 'm', 1.0, False)
        cm.add_connection('s2', 'm', 1.0, False)
        cm.add_connection('m', 't', 1.0, False)

        visualizer = ConnectionVisualizer(cm)
        sources = visualizer._get_source_nodes()

        assert 's1' in sources
        assert 's2' in sources
        assert 'm' not in sources
        assert 't' not in sources
    
    def test_get_sink_nodes(self):
        """Test : identifie correctement les puits"""
        cm = ConnectionManager()
        cm.add_connection('s', 'm', 1.0, False)
        cm.add_connection('m', 'sink1', 0.5, False)
        cm.add_connection('m', 'sink2', 0.5, False)

        visualizer = ConnectionVisualizer(cm)
        sinks = visualizer._get_sink_nodes()

        assert 'sink1' in sinks
        assert 'sink2' in sinks
        assert 'm' not in sinks
        assert 's' not in sinks

    def test_get_graph_stats(self):
        """Test : calcule les statistiques correctement"""
        cm = ConnectionManager()
        cm.add_connection('s', 't', 1.0, False)
        cm.add_connection('t', 'sink', 1.0, False)
        cm.add_connection('sink', 'source', 0.5, True)
        
        visualizer = ConnectionVisualizer(cm)
        stats = visualizer._get_graph_stats()

        assert isinstance(stats, list)
        assert len(stats) > 0

        stats_text = ' '.join(stats)
        assert '3' in stats_text
        assert '3' in stats_text
        assert '1' in stats_text

class TestComplexGraphs:
    """Tests avec des graphes complexes"""

    def test_multi_split_graph(self):
        """Test : graphe avec multiples divisions"""
        cm = ConnectionManager()
        cm.add_connection('source', 'branch1', 0.5, False)
        cm.add_connection('source', 'branch2', 0.3, False)
        cm.add_connection('source', 'branche3', 0.2, False)
        cm.add_connection('branch1', 'merge', 1.0, False)
        cm.add_connection('branch2', 'merge', 1.0, False)
        cm.add_connection('branch3', 'merge', 1.0, False)

        visualizer = ConnectionVisualizer(cm)

        for style in ['simple', 'detailed', 'tree', 'flow']:
            result = visualizer.visualize_ascii(style=style)

            assert isinstance(result, str)
            assert 'source' in result
            assert 'merge' in result

    def test_multiple_cycles(self):
        """test : graphe avec plusieurs cycles"""
        cm = ConnectionManager()
        cm.add_connection('n1', 'n2', 1.0, False)
        cm.add_connection('n2', 'n1', 0.3, True)
        cm.add_connection('n2', 'n3', 1.0, False)
        cm.add_connection('n3', 'n2', 0.2, True)

        visualizer = ConnectionVisualizer(cm)

        result = visualizer.visualize_ascii(style='detailed', highlight_cycles=True)

        assert 'cycle' in result.lower()

    def test_large_graph(self):
        """Test : graphe avec de nombreux noeuds"""
        cm = ConnectionManager()

        for i in range(9):
            cm.add_connection(f'node{i}', f'node{i+1}', 1.0, False)

        visualizer = ConnectionVisualizer(cm)

        result = visualizer.visualize_ascii(style='detailed')