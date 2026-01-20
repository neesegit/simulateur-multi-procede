"""
Module de visualisation ASCII pour ConnectionManager
"""
from typing import Dict, List, Set, Tuple, Optional
from enum import Enum

class VizStyle(Enum):
    """Styles de visualisation disponibles"""
    SIMPLE = "simple"
    DETAILED = "detailed"
    TREE = "tree"
    FLOW = "flow"

class ConnectionVisualizer:
    """Gestionnaire de visualisation pour ConnectionManager"""

    def __init__(self, connection_manager):
        self.manager = connection_manager

    def visualize_ascii(
        self,
        style: str = 'detailed',
        show_fractions: bool = True,
        show_stats: bool = True,
        highlight_cycles: bool = True
    ) -> str:
        """
        Génère une représentation ASCII du graphe avec options avancées

        Args:
            style (str, optional): Style de visualisation ('simple', 'detailed', 'tree', 'flow'). Defaults to 'detailed'.
            show_fractions (bool, optional): Afficher les fractions de débit. Defaults to True.
            show_stats (bool, optional): Afficher les statistiques. Defaults to True.
            highlight_cycles (bool, optional): %ettre en évidence les cycles. Defaults to True.

        Returns:
            str: Représentation ASCII
        """
        try:
            style_enum = VizStyle(style)
        except ValueError:
            style_enum = VizStyle.DETAILED

        if style_enum == VizStyle.SIMPLE:
            return self._visualize_simple()
        elif style_enum == VizStyle.TREE:
            return self._visualize_tree(show_fractions)
        elif style_enum == VizStyle.FLOW:
            return self._visualize_flow(show_fractions)
        else:
            return self._visualize_detailed(
                show_fractions,
                show_stats,
                highlight_cycles
            )
    
    def _visualize_simple(self) -> str:
        """Visualisation simple"""
        lines = [
            "╔═══════════════════════════════════════════════════════════╗",
            "║              GRAPHE DE CONNEXIONS                         ║",
            "╚═══════════════════════════════════════════════════════════╝",
            ""
        ]

        for node in sorted(self.manager._nodes):
            downstream = self.manager.get_downstream_nodes(node)

            if downstream:
                for target_id, conn in downstream:
                    fraction_str = (
                        f" [{conn.flow_fraction*100:.0f}%]"
                        if conn.flow_fraction < 1.0
                        else ""
                    )
                    recycle_str = " (recyclage)" if conn.is_recycle else ""

                    lines.append(
                        f"\t{node:20s} -> {target_id:20s}{fraction_str}{recycle_str}"
                    )
            else:
                lines.append(f"\t{node:20s} -> [Sortie]")

        lines.append("")
        lines.append("─"*63)
        return "\n".join(lines)
    
    def _visualize_detailed(
            self,
            show_fractions: bool,
            show_stats: bool,
            highlight_cycles: bool
    ) -> str:
        """Visualisation détaillée avec statistiques"""
        lines = [
            "╔═══════════════════════════════════════════════════════════╗",
            "║              GRAPHE DE CONNEXIONS (DETAILLE)              ║",
            "╚═══════════════════════════════════════════════════════════╝",
            ""
        ]

        if show_stats:
            lines.extend(self._get_graph_stats())
            lines.append("")

        cycles = []
        if highlight_cycles:
            cycles = self.manager.detect_cycles()
            if cycles:
                lines.append("Cycles détectés :")
                for i, cycle in enumerate(cycles, 1):
                    cycle_str = " -> ".join(cycle)
                    lines.append(f"\t[{i}] {cycle_str}")
                lines.append("")

        sources = self._get_source_nodes()
        if sources:
            lines.append("Sources :")
            for src in sorted(sources):
                lines.append(f"\t- {src}")
            lines.append("")

        lines.append("Connexions détaillées :")
        lines.append("")

        for node in sorted(self.manager._nodes):
            upstream = self.manager.get_upstream_nodes(node)
            downstream = self.manager.get_downstream_nodes(node)

            in_cycle = any(node in cycle for cycle in cycles)
            cycle_marker = " (recyclage)" if in_cycle else ""

            lines.append(f"┌─ {node}{cycle_marker}")
            if upstream:
                lines.append("│ Entrées :")
                total_in = sum(conn.flow_fraction for _, conn in upstream)
                for src_id, conn in upstream:
                    frac_str = f"{conn.flow_fraction*100:.1f}%" if show_fractions else ""
                    rec_str = " [R]" if conn.is_recycle else ""
                    lines.append(f"│\t<- {src_id:20s} {frac_str:>6s}{rec_str}")
                lines.append(f"│\tTotal entrant: {total_in*100:.1f}%")
            else:
                lines.append("│\t(aucune entrée)")

            if downstream:
                lines.append("│ Sorties :")
                total_out = sum(
                    conn.flow_fraction for _, conn in downstream
                    if not conn.is_recycle
                )
                for tgt_id, conn in downstream:
                    frac_str = f"{conn.flow_fraction*100:.1f}%" if show_fractions else ""
                    rec_str = " [R]" if conn.is_recycle else ""
                    lines.append(f"│\t-> {tgt_id:20s} {frac_str:>6s}{rec_str}")
                lines.append(f"│\tTotal sortant : {total_out*100:.1f}%")
            else:
                lines.append("│ (sortie finale)")
            
            lines.append("└─")
            lines.append("")
        lines.append("─"*63)
        lines.append("Légende : [R] = Recyclage")

        return "\n".join(lines)
    
    def _visualize_tree(self, show_fractions: bool) -> str:
        """Visualisation en arbre hiérarchique"""
        lines = [
            "╔═══════════════════════════════════════════════════════════╗",
            "║              GRAPHE DE CONNEXIONS (Arbre)                 ║",
            "╚═══════════════════════════════════════════════════════════╝",
            ""
        ]

        sources = self._get_source_nodes()

        if not sources:
            lines.append("Aucun noeud source détecté")
            return "\n".join(lines)
        
        visited = set()

        for source in sorted(sources):
            lines.extend(
                self._build_tree_recursive(source, "", True, visited, show_fractions)
            )
            lines.append("")

        return "\n".join(lines)
    
    def _build_tree_recursive(
            self,
            node: str,
            prefix: str,
            is_last: bool,
            visited: Set[str],
            show_fractions: bool
    ) -> List[str]:
        """Construit récursivement l'arbre"""
        lines = []

        connector = "└── " if is_last else "├── "
        extension = "    " if is_last else "│   "

        cycle_marker = " (déjà visité)" if node in visited else ""
        lines.append(f"{prefix}{connector}{node}{cycle_marker}")

        if node in visited:
            return lines
        
        visited.add(node)

        downstream = self.manager.get_downstream_nodes(node)
        child_prefix = prefix + extension

        for i, (child_id, conn) in enumerate(downstream):
            is_last_child = (i == len(downstream) - 1)

            frac_info = ""
            if show_fractions and conn.flow_fraction < 1.0:
                frac_info = f" [{int(conn.flow_fraction*100)}%]"

            rec_info = " [R]" if conn.is_recycle else ""

            child_visited_marker = (
                " (déjà visité)" if child_id in visited else ""
            )

            lines.append(
                    f"{child_prefix}{'└── ' if is_last_child else '├── '}"
                    f"{child_id}{frac_info}{rec_info}{child_visited_marker}"
                )

            if not conn.is_recycle and child_id not in visited:
                lines.extend(
                    self._build_tree_recursive(
                        child_id,
                        child_prefix,
                        is_last_child,
                        visited,
                        show_fractions
                    )
                )
                
        return lines
    
    def _visualize_flow(self, show_fractions: bool) -> str:
        """Visualisation type diagramme de flux"""
        lines = [
            "╔═══════════════════════════════════════════════════════════╗",
            "║              GRAPHE DE CONNEXIONS (Séquentiel)            ║",
            "╚═══════════════════════════════════════════════════════════╝",
            ""
        ]

        try:
            execution_order = self.manager.get_execution_order()
        except ValueError as e:
            lines.append(f"Impossible de calculer l'ordre d'exécution : {e}")
            return "\n".join(lines)
        
        for i, node in enumerate(execution_order):
            downstream = self.manager.get_downstream_nodes(node)

            lines.append("┌" + "─"*40 + "┐")
            lines.append(f"│ {node:^38s} │")
            lines.append("└" + "─"*40 + "┘")

            if downstream:
                non_recycle = [
                    (t, c) for t, c in downstream if not c.is_recycle
                ]
                recycle = [
                    (t, c) for t, c in downstream if c.is_recycle
                ]

                for target_id, conn in non_recycle:
                    frac = f" {conn.flow_fraction*100:.0f}%" if show_fractions else ""
                    lines.append(f"\t│{frac}")
                    lines.append("\t▼")

                for target_id, conn in recycle:
                    frac = f"{conn.flow_fraction*100:.0f}%" if show_fractions else ""
                    lines.append(f"\t├──(recycle)──▶ {target_id} ({frac})")
            else:
                lines.append("\t│")
                lines.append("\t▼")
                lines.append("\t[FIN]")

            lines.append("")
        
        return "\n".join(lines)

    def _get_graph_stats(self) -> List[str]:
        """Génère les statistiques du graphe"""
        stats = []

        stats.append("Statistiques :")
        stats.append(f"\t- Noeuds totaux : {len(self.manager._nodes)}")
        stats.append(f"\t- Connexions totales : {len(self.manager._connections)}")

        recycle_count = sum(1 for c in self.manager._connections if c.is_recycle)
        stats.append(f"\t- Recyclages : {recycle_count}")

        sources = self._get_source_nodes()
        sinks = self._get_sink_nodes()
        stats.append(f"\t- Noeuds sources : {len(sources)}")
        stats.append(f"\t- Noeuds puits : {len(sinks)}")

        cycles = self.manager.detect_cycles()
        if cycles:
            stats.append(f"\t- Cycles détectés : {len(cycles)}")
        
        return stats
    
    def _get_source_nodes(self) -> Set[str]:
        """Identifie les noeuds sans entrée"""
        nodes_with_input = set()
        for conn in self.manager._connections:
            if not conn.is_recycle:
                nodes_with_input.add(conn.target_id)
        return self.manager._nodes - nodes_with_input
    
    def _get_sink_nodes(self) -> Set[str]:
        """Identifie les noeuds sans sortie"""
        nodes_with_output = set()
        for conn in self.manager._connections:
            nodes_with_output.add(conn.source_id)

        return self.manager._nodes - nodes_with_output