import pytest
from unittest.mock import Mock, patch

from core.connection.connection_manager import ConnectionManager
from core.connection.connection import Connection


class TestConnectionManager:
    """Tests ConnectionManager"""

    def test_initialization(self):
        """Test : initialisation"""
        manager = ConnectionManager()

        assert manager._connections == []
        assert manager._nodes == set()

    def test_add_single_connection(self):
        """Test : ajout d'une connexion simple"""
        manager = ConnectionManager()

        manager.add_connection('source1', 'target1', 1.0, False)

        assert len(manager._connections) == 1
        assert 'source1' in manager._nodes
        assert 'target1' in manager._nodes

    def test_add_multiple_connections(self):
        """Test : ajout de plusieurs connextions"""
        manager = ConnectionManager()

        manager.add_connection('source1', 'target1', 1.0, False)
        manager.add_connection('source2', 'target2', 0.5, False)

        assert len(manager._connections) == 2
        assert len(manager._nodes) == 4

    def test_add_connection_with_fraction(self):
        """Test : connexion avec fraction"""
        manager = ConnectionManager()

        manager.add_connection('source1', 'target1', 0.7, False)

        conn = manager._connections[0]
        assert conn.flow_fraction == 0.7

    @patch('core.connection.connection_manager.logger')
    def test_add_connection_logs(self, mock_logger):
        """Test : add_conenction log l'ajout"""
        manager = ConnectionManager()

        manager.add_connection('source', 'target', 1.0, False)

        mock_logger.debug.assert_called()

class TestConnectionManagerValidation:
    """Tests de validation"""

    def test_invalid_fraction_greater_than_one(self):
        """Test : fraction > 1 invalide"""
        manager = ConnectionManager()

        with pytest.raises(ValueError, match='flow_fraction'):
            manager.add_connection('source', 'target', flow_fraction=1.5)

    def test_invalid_fraction_zero(self):
        """Test : fraction zéro invalide"""
        manager = ConnectionManager()

        with pytest.raises(ValueError, match='flow_fraction'):
            manager.add_connection('source', 'target', flow_fraction=0.0)

    def test_invalid_fraction_negative(self):
        """Test : fraction négative invalide"""
        manager = ConnectionManager()
        
        with pytest.raises(ValueError, match='flow_fraction'):
            manager.add_connection('source', 'target', flow_fraction=-0.5)

    def test_add_connection_rejects_self_loop(self):
        """Test : rejette les boucles sur soi-même"""
        manager = ConnectionManager()

        with pytest.raises(ValueError, match='différents'):
            manager.add_connection('node1', 'node1')

    def test_validate_detects_fraction_overflow(self):
        """Test : validate détecte les fractions > 1"""
        manager = ConnectionManager()

        manager.add_connection('source', 'target1', 0.6)
        manager.add_connection('source', 'target2', 0.5)

        validation = manager.validate()

        assert len(validation['errors']) > 0
        assert any('fraction' in err for err in validation['errors'])

    def test_validate_fraction_sum_exactly_one(self):
        """Test : somme exactement 1 est valide"""
        manager = ConnectionManager()

        manager.add_connection('s', 't1', 0.6, False)
        manager.add_connection('s', 't2', 0.4, False)

        validation = manager.validate()

        assert len(validation['errors']) == 0

    def test_validate_recycle_connections_allowed(self):
        """Test : recyclages autorisés même si créent un cycle"""
        manager = ConnectionManager()

        manager.add_connection('p1', 'p2', 1.0, False)
        manager.add_connection('p2', 'p1', 0.3, True)

        validation = manager.validate()

        assert len(validation['errors']) == 0

class TestConnectionManagerTopology:
    """Tests de topologie du graphe"""

    def test_get_upstream_nodes_single(self):
        """Test : un seul noeud en amont"""
        manager = ConnectionManager()

        manager.add_connection('source', 'target', 1.0, False)

        upstream = manager.get_upstream_nodes('target')

        assert len(upstream) == 1
        assert upstream[0][0] == 'source'

    def test_get_upstream_nodes_multiple(self):
        """Test : plusieurs noeuds en amont"""
        manager = ConnectionManager()

        manager.add_connection('source1', 'target', 0.5)
        manager.add_connection('source2', 'target', 0.5)

        upstream = manager.get_upstream_nodes('target')

        assert len(upstream) == 2
        source_ids = [s for s, _ in upstream]
        assert 'source1' in source_ids
        assert 'source2' in source_ids

    def test_get_upstream_nodes_none(self):
        """Test : aucun noeud en amont"""
        manager = ConnectionManager()

        manager.add_connection('source', 'target', 1.0, False)

        upstream = manager.get_upstream_nodes('source')

        assert len(upstream) == 0

    def test_get_downstream_nodes_single(self):
        """Test : un seul noeud en aval"""
        manager = ConnectionManager()

        manager.add_connection('source', 'target', 1.0, False)

        downstream = manager.get_downstream_nodes('source')

        assert len(downstream) == 1
        assert downstream[0][0] == 'target'

    def test_get_downstream_nodes_multiple(self):
        """Test : plusieurs noeuds en aval"""
        manager = ConnectionManager()

        manager.add_connection('source', 'target1', 0.6, False)
        manager.add_connection('source', 'target2', 0.4, False)

        downstream = manager.get_downstream_nodes('source')

        assert len(downstream) == 2
        target_ids = [t for t, _ in downstream]
        assert 'target1' in target_ids
        assert 'target2' in target_ids

class TestExecutionOrder:
    """Tests du tri topologique"""

    def test_sequential_chain(self):
        """Test : chaîne séquentielle simple"""
        manager = ConnectionManager()

        manager.add_connection('influent', 'p1', 1.0, False)
        manager.add_connection('p1', 'p2', 1.0, False)
        manager.add_connection('p2', 'p3', 1.0, False)

        order = manager.get_execution_order()

        assert order == ['influent', 'p1', 'p2', 'p3']

    def test_parallel_branches(self):
        """Test : branches parallèles"""
        manager = ConnectionManager()

        manager.add_connection('influent', 'p1', 0.5, False)
        manager.add_connection('influent', 'p2', 0.5, False)
        manager.add_connection('p1', 'p3', 1.0, False)
        manager.add_connection('p2', 'p3', 1.0, False)

        order = manager.get_execution_order()

        assert order[0] == 'influent'
        assert order[-1] == 'p3'
        assert 'p1' in order
        assert 'p2' in order

    def test_execution_order_with_recycle(self):
        """test : ordre d'exécution avec recyclage"""
        manager = ConnectionManager()

        manager.add_connection('influent', 'p1', 1.0, False)
        manager.add_connection('p1', 'p2', 1.0, False)
        manager.add_connection('p2', 'p1', 0.3, True)

        order = manager.get_execution_order()

        assert order == ['influent', 'p1', 'p2']

    def test_execution_order_cycle_without_recycle_flag(self):
        """Test : cycle sans flag recyclage lève une erreur"""
        manager = ConnectionManager()

        manager.add_connection('p1', 'p2', 1.0, False)
        manager.add_connection('p2', 'p3', 1.0, False)
        manager.add_connection('p3', 'p1', 1.0, False)

        with pytest.raises(ValueError, match='Cycle'):
            manager.get_execution_order()

class TestCycleDetection:
    """Tests de détection de cycles"""

    def test_detect_simple_cycle(self):
        """Test : détection d'un cycle simple"""
        manager = ConnectionManager()

        manager.add_connection('p1', 'p2', 1.0, True)
        manager.add_connection('p2', 'p3', 1.0, True)
        manager.add_connection('p3', 'p1', 1.0, True)

        cycles = manager.detect_cycles()

        assert len(cycles) > 0

    def test_detect_no_cycle(self):
        """Test : pas de cycle détecté"""
        manager = ConnectionManager()

        manager.add_connection('influent', 'p1', 1.0, False)
        manager.add_connection('p1', 'p2', 1.0, False)

        cycles = manager.detect_cycles()

        assert len(cycles) == 0

class Testvisualization:
    """Tests de visualisation"""

    def test_visualize_ascii_simple(self):
        """Test : visualisation ASCII simple"""
        manager = ConnectionManager()

        manager.add_connection('influent', 'p1', 1.0, False)
        manager.add_connection('p1', 'p2', 0.7, False)

        ascii_repr = manager.visualize_ascii()