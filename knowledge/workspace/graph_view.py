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


def _document_id_for_source(source_id: str) -> str | None:
    if source_id.startswith("SRC-"):
        return f"DOC-{source_id[4:]}"
    return None


def _resolve_node_id(node_id: str, alias: dict[str, str]) -> str:
    return alias.get(node_id, node_id)


def _entity_node(workspace: KnowledgeWorkspace, entity_id: str) -> dict[str, object]:
    return {
        "id": entity_id,
        "label": entity_id,
        "kind": "entity",
        "summary": "Engineering entity",
        "project_id": workspace.project_id,
        "format": "entity",
        "rights_status": "INTERNAL",
        "keywords": [],
    }


def build_knowledge_graph(workspace: KnowledgeWorkspace) -> dict[str, object]:
    if workspace.seed_corpus_enabled:
        workspace._ensure_seed_corpus()

    node_index: dict[str, dict[str, object]] = {}
    edges: list[dict[str, object]] = []
    seen_concept_edges: set[tuple[str, str, str]] = set()
    seen_document_links: set[tuple[str, str]] = set()

    sources = workspace.list_sources()
    keyword_map: dict[str, set[str]] = {}
    alias: dict[str, str] = {}

    for source in sources:
        summary = (source.recovered_text or source.title or source.filename)[:220].strip()
        keywords = _keywords(source.recovered_text or source.title or source.filename)
        keyword_map[source.source_id] = set(keywords)
        node_index[source.source_id] = {
            "id": source.source_id,
            "label": source.title or source.filename,
            "kind": "document",
            "summary": summary,
            "project_id": source.project_id,
            "format": source.workspace_format,
            "rights_status": source.rights_status,
            "keywords": list(keywords),
        }
        alias[source.source_id] = source.source_id
        document_id = _document_id_for_source(source.source_id)
        if document_id is not None:
            alias[document_id] = source.source_id

    def ensure_node(node_id: str) -> None:
        if node_id in node_index:
            return
        node_index[node_id] = _entity_node(workspace, node_id)

    for edge in workspace.service.graph.edges:
        source_id = _resolve_node_id(edge.source_id, alias)
        target = _resolve_node_id(edge.target_id, alias)
        if source_id == target:
            continue
        relationship = edge.relationship.value
        key = (source_id, target, relationship)
        if key in seen_concept_edges:
            continue
        seen_concept_edges.add(key)
        ensure_node(source_id)
        ensure_node(target)
        edges.append(
            {
                "source": source_id,
                "target": target,
                "relationship": relationship,
                "kind": "concept",
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
            link_key = (left, right) if left <= right else (right, left)
            if link_key in seen_document_links:
                continue
            seen_document_links.add(link_key)
            edges.append(
                {
                    "source": link_key[0],
                    "target": link_key[1],
                    "relationship": "RELATED_TO",
                    "kind": "document-link",
                    "shared_terms": sorted(shared)[:5],
                },
            )

    nodes = list(node_index.values())
    renderable_edges = [
        edge
        for edge in edges
        if edge["source"] in node_index and edge["target"] in node_index
    ]
    return {
        "nodes": nodes,
        "edges": renderable_edges,
        "node_count": len(nodes),
        "edge_count": len(renderable_edges),
    }
