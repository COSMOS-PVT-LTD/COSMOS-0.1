"""Interactive knowledge graph view model for Maharshi Bharadwaj UI."""

from __future__ import annotations

import re

from knowledge.workspace.session import KnowledgeWorkspace

__all__ = ("build_knowledge_graph",)

_TOKEN = re.compile(r"[a-zA-Z][a-zA-Z0-9_\-]{2,}")


def _keywords(text: str, limit: int = 12) -> tuple[str, ...]:
    counts: dict[str, int] = {}
    for match in _TOKEN.finditer(text.lower()):
        token = match.group(0)
        if token in {"the", "and", "for", "with", "from", "that", "this", "document"}:
            continue
        counts[token] = counts.get(token, 0) + 1
    ranked = sorted(counts.items(), key=lambda item: (-item[1], item[0]))
    return tuple(token for token, _count in ranked[:limit])


def build_knowledge_graph(workspace: KnowledgeWorkspace) -> dict[str, object]:
    workspace._ensure_seed_corpus()
    nodes: list[dict[str, object]] = []
    edges: list[dict[str, object]] = []
    seen_edges: set[tuple[str, str]] = set()

    sources = workspace.list_sources()
    keyword_map: dict[str, set[str]] = {}

    for source in sources:
        summary = (source.recovered_text or source.title or source.filename)[:220].strip()
        keywords = _keywords(source.recovered_text or source.title or source.filename)
        keyword_map[source.source_id] = set(keywords)
        nodes.append(
            {
                "id": source.source_id,
                "label": source.title or source.filename,
                "kind": "document",
                "summary": summary,
                "project_id": source.project_id,
                "format": source.workspace_format,
                "rights_status": source.rights_status,
                "keywords": list(keywords),
            },
        )

    for edge in workspace.service.graph.edges:
        key = (edge.source_id, edge.target_id)
        if key in seen_edges:
            continue
        seen_edges.add(key)
        edges.append(
            {
                "source": edge.source_id,
                "target": edge.target_id,
                "relationship": edge.relationship.value,
                "kind": "concept",
            },
        )
        if not any(node["id"] == edge.source_id for node in nodes):
            nodes.append(
                {
                    "id": edge.source_id,
                    "label": edge.source_id,
                    "kind": "entity",
                    "summary": "Engineering entity",
                    "project_id": workspace.project_id,
                    "format": "entity",
                    "rights_status": "INTERNAL",
                    "keywords": [],
                },
            )
        if not any(node["id"] == edge.target_id for node in nodes):
            nodes.append(
                {
                    "id": edge.target_id,
                    "label": edge.target_id,
                    "kind": "entity",
                    "summary": "Engineering entity",
                    "project_id": workspace.project_id,
                    "format": "entity",
                    "rights_status": "INTERNAL",
                    "keywords": [],
                },
            )

    source_ids = [source.source_id for source in sources]
    for index, left in enumerate(source_ids):
        left_keys = keyword_map.get(left, set())
        if not left_keys:
            continue
        for right in source_ids[index + 1 :]:
            shared = left_keys.intersection(keyword_map.get(right, set()))
            if not shared:
                continue
            key = tuple(sorted((left, right)))
            if key in seen_edges:
                continue
            seen_edges.add(key)
            edges.append(
                {
                    "source": key[0],
                    "target": key[1],
                    "relationship": "RELATED_TO",
                    "kind": "document-link",
                    "shared_terms": sorted(shared)[:5],
                },
            )

    return {"nodes": nodes, "edges": edges, "node_count": len(nodes), "edge_count": len(edges)}
