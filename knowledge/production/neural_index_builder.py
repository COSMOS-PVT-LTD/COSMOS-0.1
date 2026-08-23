"""Production neural vector index builder (additive — does not modify W7IndexBuilder)."""

from __future__ import annotations

from knowledge.embeddings.protocol import EmbeddingBackend
from knowledge.graph.contracts import GraphNode
from knowledge.graph.repository import GraphStore
from knowledge.graph.serialization import canonical_graph_record_digest
from knowledge.indexing.w7.bundle import W7IndexBuilder, W7IndexBundle
from knowledge.indexing.w7.vector import VectorRecord, build_vector_index_from_records

__all__ = ("build_production_index_bundle",)


def _node_text(node: GraphNode) -> str:
    parts: list[str] = [node.node_type]

    for key in ("extracted_label", "canonical_name", "document_id"):
        value = node.properties.get(key)

        if isinstance(value, str) and value.strip():
            parts.append(value)

    return " ".join(parts)


def build_production_index_bundle(
    store: GraphStore,
    embedding_backend: EmbeddingBackend,
) -> W7IndexBundle:
    """Build a W7 bundle with neural/deterministic vectors from node text."""

    dimension = embedding_backend.identity.dimension
    base_bundle = W7IndexBuilder(vector_dimension=dimension).build(store)
    source_digest = canonical_graph_record_digest(store.snapshot())
    records: list[VectorRecord] = []

    for node in store.list_nodes():
        vector = embedding_backend.embed_document(_node_text(node))
        records.append(
            VectorRecord(
                record_id=f"VEC-{node.node_id}",
                target_id=node.node_id,
                target_type=node.node_type,
                vector=vector,
                document_id=(
                    str(node.properties["document_id"])
                    if isinstance(node.properties.get("document_id"), str)
                    else None
                ),
                lifecycle_state=(
                    str(node.properties["lifecycle_state"])
                    if isinstance(node.properties.get("lifecycle_state"), str)
                    else None
                ),
            ),
        )

    vector_index = build_vector_index_from_records(
        index_id=f"vector-{embedding_backend.identity.model_id}",
        source_digest=source_digest,
        records=records,
    )

    return W7IndexBundle(
        source_digest=base_bundle.source_digest,
        lexical_semantic_bundle=base_bundle.lexical_semantic_bundle,
        vector_index=vector_index,
        graph_index=base_bundle.graph_index,
        lifecycle_state=base_bundle.lifecycle_state,
    )
