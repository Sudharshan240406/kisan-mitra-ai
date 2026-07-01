import time
from typing import Any

from pydantic import BaseModel, Field


class ReasoningNode(BaseModel):
    """
    Individual node in the multi-agent reasoning trace.
    """
    node_id: str = Field(..., description="Unique node tracking identifier.")
    parent_id: str | None = Field(default=None, description="Parent node tracking identifier.")
    children_ids: list[str] = Field(default_factory=list, description="Children node references list.")
    node_type: str = Field(..., description="Classification category (e.g. Query, Intent, Workflow, Agent, Decision, Output).")
    evidence_id: str | None = Field(default=None, description="Associated Evidence object ID.")
    confidence: float | None = Field(default=None, description="Confidence rating recorded at this node.")
    timestamp: float = Field(default_factory=time.time, description="Creation timestamp.")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Extensible JSON metadata properties.")

class ReasoningGraph(BaseModel):
    """
    Directed graph representing the multi-agent reasoning execution history.
    """
    graph_id: str = Field(..., description="Unique graph tracking identifier.")
    root_node_id: str = Field(..., description="The entry query node identifier.")
    nodes: dict[str, ReasoningNode] = Field(default_factory=dict, description="Nodes storage mapping.")

    def add_node(self, node: ReasoningNode) -> None:
        self.nodes[node.node_id] = node
        if node.parent_id and node.parent_id in self.nodes:
            parent = self.nodes[node.parent_id]
            if node.node_id not in parent.children_ids:
                parent.children_ids.append(node.node_id)
        logger_name = f"kisan_mitra_ai.reasoning_graph.{self.graph_id}"
        import logging
        logging.getLogger(logger_name).debug(f"Added reasoning node: '{node.node_id}' ({node.node_type})")

    def traverse(self) -> list[ReasoningNode]:
        """
        Traverses the graph using Breadth-First Search (BFS) starting from the root node.
        """
        visited = set()
        queue = [self.root_node_id]
        traversal_order = []

        while queue:
            curr_id = queue.pop(0)
            if curr_id in visited:
                continue

            node = self.nodes.get(curr_id)
            if node:
                visited.add(curr_id)
                traversal_order.append(node)
                # Queue children nodes
                for child in node.children_ids:
                    if child not in visited:
                        queue.append(child)

        return traversal_order

    def export(self) -> dict[str, Any]:
        """
        Exports the graph to a visualization-ready JSON structure.
        """
        return self.model_dump()

    def validate_graph(self) -> bool:
        """
        Structural validation: checks for cycle presence and disconnected nodes.
        """
        if self.root_node_id not in self.nodes:
            return False

        # Check cycles using DFS
        visited = set()
        rec_stack = set()

        def has_cycle(node_id: str) -> bool:
            visited.add(node_id)
            rec_stack.add(node_id)

            node = self.nodes.get(node_id)
            if node:
                for child in node.children_ids:
                    if child not in visited:
                        if has_cycle(child):
                            return True
                    elif child in rec_stack:
                        return True
            rec_stack.remove(node_id)
            return False

        if has_cycle(self.root_node_id):
            return False # Cycle detected

        # Ensure all nodes are reachable from root
        return len(visited) == len(self.nodes)

    def replay(self) -> list[str]:
        """
        Generates step execution logs mapping node traversal.
        """
        ordered = self.traverse()
        replay_logs = []
        for node in ordered:
            conf_str = f" [Confidence: {node.confidence:.2f}]" if node.confidence is not None else ""
            replay_logs.append(
                f"[{node.node_type}] Node '{node.node_id}' processed at {node.timestamp:.2f}{conf_str}."
            )
        return replay_logs

    def replay_conversation(self) -> list[str]:
        """
        Generates transition steps logs mapping conversational timeline.
        """
        ordered = self.traverse()
        logs = []
        for node in ordered:
            if node.node_type == "Conversation":
                state = node.metadata.get("state", "Unknown")
                logs.append(f"Conversation transition to state '{state}' logged at {node.timestamp:.2f}.")
        return logs

    def replay_reasoning(self) -> list[str]:
        """
        Generates diagnostic steps mapping active agent reasonings.
        """
        ordered = self.traverse()
        logs = []
        for node in ordered:
            if node.node_type in ["Decision", "Agent", "Evidence"]:
                conf_str = f" with confidence {node.confidence:.2f}" if node.confidence is not None else ""
                logs.append(f"[{node.node_type}] Node '{node.node_id}' resolved{conf_str}.")
        return logs

    def get_visualization_metadata(self) -> dict[str, Any]:
        """
        Retrieves structure parameters detailing node linkages for UI rendering.
        """
        nodes_info = []
        links = []
        for node_id, node in self.nodes.items():
            nodes_info.append({
                "id": node_id,
                "type": node.node_type,
                "confidence": node.confidence,
                "timestamp": node.timestamp,
                "label": f"{node.node_type}: {node_id}"
            })
            for child in node.children_ids:
                links.append({
                    "source": node_id,
                    "target": child,
                    "relation": "parent-to-child"
                })

        return {
            "graph_id": self.graph_id,
            "root_node_id": self.root_node_id,
            "nodes": nodes_info,
            "links": links
        }
