import logging
from typing import Any, Optional

logger = logging.getLogger("kisan_mitra_ai.knowledge.graph")


class GraphNode:
    """
    Representation of an entity node in the Knowledge Graph.
    """
    def __init__(self, node_id: str, node_type: str, properties: Optional[dict[str, Any]] = None) -> None:
        self.id = node_id
        self.type = node_type
        self.properties = properties or {}

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "type": self.type,
            "properties": self.properties
        }


class GraphEdge:
    """
    Representation of a directed relation edge between nodes.
    """
    def __init__(self, source: str, target: str, edge_type: str, properties: Optional[dict[str, Any]] = None) -> None:
        self.source = source
        self.target = target
        self.type = edge_type
        self.properties = properties or {}

    def to_dict(self) -> dict[str, Any]:
        return {
            "source": self.source,
            "target": self.target,
            "type": self.type,
            "properties": self.properties
        }


class KnowledgeGraph:
    """
    Graph containing agricultural entity relationships and traversal reasoning methods.
    """
    def __init__(self) -> None:
        self.nodes: dict[str, GraphNode] = {}
        self.edges: list[GraphEdge] = []
        # Adjacency lists for fast traversals
        self._adj: dict[str, list[GraphEdge]] = {}

    def add_node(self, node_id: str, node_type: str, properties: Optional[dict[str, Any]] = None) -> None:
        self.nodes[node_id] = GraphNode(node_id, node_type, properties)
        if node_id not in self._adj:
            self._adj[node_id] = []

    def add_edge(self, source: str, target: str, edge_type: str, properties: Optional[dict[str, Any]] = None) -> None:
        if source not in self.nodes:
            self.add_node(source, "Unknown")
        if target not in self.nodes:
            self.add_node(target, "Unknown")

        edge = GraphEdge(source, target, edge_type, properties)
        self.edges.append(edge)
        self._adj[source].append(edge)
        logger.debug(f"KnowledgeGraph: Added edge {source} --[{edge_type}]--> {target}")

    def get_neighbors(self, node_id: str, edge_type: Optional[str] = None) -> list[dict[str, Any]]:
        """
        Retrieves all adjacent nodes connected by a specific relation type.
        """
        neighbors = []
        for edge in self._adj.get(node_id, []):
            if edge_type is None or edge.type == edge_type:
                neighbors.append({
                    "node": self.nodes[edge.target].to_dict(),
                    "edge": edge.to_dict()
                })
        return neighbors

    def find_paths(self, start_id: str, end_id: str, max_depth: int = 3) -> list[list[dict[str, Any]]]:
        """
        Executes a DFS search path matching to explain relations.
        """
        paths: list[list[dict[str, Any]]] = []
        if start_id not in self.nodes or end_id not in self.nodes:
            return paths

        def dfs(curr: str, target: str, visited: set[str], current_path: list[dict[str, Any]], depth: int) -> None:
            if depth > max_depth:
                return
            if curr == target:
                paths.append(list(current_path))
                return

            visited.add(curr)
            for edge in self._adj.get(curr, []):
                next_node = edge.target
                if next_node not in visited:
                    current_path.append({
                        "source": curr,
                        "target": next_node,
                        "relation": edge.type,
                        "properties": edge.properties
                    })
                    dfs(next_node, target, visited, current_path, depth + 1)
                    current_path.pop()
            visited.remove(curr)

        dfs(start_id, end_id, set(), [], 0)
        return paths

    def explain_paths(self, start_id: str, end_id: str, max_depth: int = 3) -> list[str]:
        """
        Builds explainable natural language reasoning sequences from graph paths.
        """
        paths = self.find_paths(start_id, end_id, max_depth)
        explanations = []
        for path in paths:
            steps = []
            for step in path:
                src_name = self.nodes[step["source"]].properties.get("name", step["source"])
                tgt_name = self.nodes[step["target"]].properties.get("name", step["target"])
                rel = step["relation"].lower().replace("_", " ")
                steps.append(f"{src_name} is {rel} {tgt_name}")
            explanations.append(" because " + " and ".join(steps))
        return explanations

    def health(self) -> dict[str, Any]:
        return {
            "provider": "KnowledgeGraph",
            "status": "healthy",
            "nodes_count": len(self.nodes),
            "edges_count": len(self.edges)
        }
