"""Graph adjacency export."""

from __future__ import annotations

import json

from knowledge.graph.concept_graph import ConceptGraph

__all__ = ("export_graph",)


def export_graph(graph: ConceptGraph) -> str:
    payload = {
        "provenance": "concept-graph",
        "edges": [
            {
                "relationship": edge.relationship.value,
                "source_id": edge.source_id,
                "target_id": edge.target_id,
            }
            for edge in graph._edges
        ],
    }
    return json.dumps(payload, indent=2, sort_keys=True)
