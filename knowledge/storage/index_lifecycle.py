"""W7 index persistence lifecycle operations (Step 7)."""

from __future__ import annotations

import json
from dataclasses import dataclass
from enum import Enum
from pathlib import Path

from knowledge.embeddings.identity import EmbeddingModelIdentity
from knowledge.graph.repository import GraphStore
from knowledge.graph.serialization import canonical_graph_record_digest
from knowledge.indexing.exceptions import IndexStaleError, IndexValidationError
from knowledge.indexing.models import IndexEntry, IndexLifecycleState
from knowledge.indexing.lexical import InMemoryLexicalIndex
from knowledge.indexing.semantic import InMemorySemanticIndex
from knowledge.indexing.w7.bundle import W7IndexBuilder, W7IndexBundle
from knowledge.indexing.w7.graph_index import GraphIndexAdjacency, InMemoryGraphIndex
from knowledge.indexing.w7.vector import InMemoryVectorIndex, VectorRecord
from knowledge.storage.exceptions import CorruptionError, SchemaMismatchError
from knowledge.storage.schema import INDEX_BUNDLE_FORMAT_VERSION

__all__ = (
    "IndexLifecycleManager",
    "IndexLifecycleOperation",
    "PersistedIndexBundle",
)


class IndexLifecycleOperation(Enum):
    """Explicit index lifecycle operations."""

    BUILD = "BUILD"
    LOAD = "LOAD"
    VALIDATE = "VALIDATE"
    INVALIDATE = "INVALIDATE"
    REBUILD = "REBUILD"


@dataclass(frozen=True, slots=True, kw_only=True)
class PersistedIndexBundle:
    """Serialized index bundle metadata and payloads."""

    format_version: str
    source_digest: str
    embedding_model: EmbeddingModelIdentity
    lifecycle_state: IndexLifecycleState
    lexical_entries: tuple[dict[str, object], ...]
    semantic_entries: tuple[dict[str, object], ...]
    vector_records: tuple[dict[str, object], ...]
    graph_adjacency: tuple[dict[str, object], ...]
    schema_version: str = "1.0.0"
    index_version: str = "1.0.0"
    embedding_backend: str | None = None
    embedding_configuration_hash: str | None = None
    corpus_version: str = "1.0.0"

    def to_mapping(self) -> dict[str, object]:
        payload: dict[str, object] = {
            "corpus_version": self.corpus_version,
            "embedding_model": self.embedding_model.to_mapping(),
            "format_version": self.format_version,
            "graph_adjacency": list(self.graph_adjacency),
            "index_version": self.index_version,
            "lexical_entries": list(self.lexical_entries),
            "lifecycle_state": self.lifecycle_state.value,
            "schema_version": self.schema_version,
            "semantic_entries": list(self.semantic_entries),
            "source_digest": self.source_digest,
            "vector_records": list(self.vector_records),
        }

        if self.embedding_backend is not None:
            payload["embedding_backend"] = self.embedding_backend

        if self.embedding_configuration_hash is not None:
            payload["embedding_configuration_hash"] = self.embedding_configuration_hash

        return payload

    @classmethod
    def from_mapping(cls, data: dict[str, object]) -> PersistedIndexBundle:
        embedding_raw = data.get("embedding_model")

        if not isinstance(embedding_raw, dict):
            raise CorruptionError("Persisted index bundle missing embedding_model.")

        def _dict_items(key: str) -> tuple[dict[str, object], ...]:
            raw = data.get(key, ())
            if not isinstance(raw, list):
                return ()
            return tuple(item for item in raw if isinstance(item, dict))

        return cls(
            format_version=str(data["format_version"]),
            source_digest=str(data["source_digest"]),
            embedding_model=EmbeddingModelIdentity.from_mapping(embedding_raw),
            lifecycle_state=IndexLifecycleState(str(data["lifecycle_state"])),
            lexical_entries=_dict_items("lexical_entries"),
            semantic_entries=_dict_items("semantic_entries"),
            vector_records=_dict_items("vector_records"),
            graph_adjacency=_dict_items("graph_adjacency"),
            schema_version=str(data.get("schema_version", "1.0.0")),
            index_version=str(data.get("index_version", "1.0.0")),
            embedding_backend=(
                str(data["embedding_backend"])
                if data.get("embedding_backend") is not None
                else None
            ),
            embedding_configuration_hash=(
                str(data["embedding_configuration_hash"])
                if data.get("embedding_configuration_hash") is not None
                else None
            ),
            corpus_version=str(data.get("corpus_version", "1.0.0")),
        )


def _entry_from_mapping(data: dict[str, object]) -> IndexEntry:
    terms_raw = data.get("terms", [])
    terms = tuple(str(term) for term in terms_raw) if isinstance(terms_raw, list) else ()

    return IndexEntry(
        entry_id=str(data["entry_id"]),
        target_id=str(data["target_id"]),
        target_type=str(data["target_type"]),
        terms=terms,
        document_id=str(data["document_id"]) if data.get("document_id") else None,
        lifecycle_state=(
            str(data["lifecycle_state"]) if data.get("lifecycle_state") else None
        ),
    )


def _vector_from_mapping(data: dict[str, object]) -> VectorRecord:
    vector_raw = data.get("vector", [])

    if not isinstance(vector_raw, list):
        raise CorruptionError("Vector record missing vector components.")

    return VectorRecord(
        record_id=str(data["record_id"]),
        target_id=str(data["target_id"]),
        target_type=str(data["target_type"]),
        vector=tuple(float(item) for item in vector_raw),
        document_id=str(data["document_id"]) if data.get("document_id") else None,
        lifecycle_state=(
            str(data["lifecycle_state"]) if data.get("lifecycle_state") else None
        ),
    )


def _adjacency_from_mapping(data: dict[str, object]) -> GraphIndexAdjacency:
    neighbors = data.get("neighbor_ids", [])
    relationships = data.get("relationship_ids", [])

    return GraphIndexAdjacency(
        node_id=str(data["node_id"]),
        node_type=str(data["node_type"]),
        neighbor_ids=tuple(str(item) for item in neighbors)
        if isinstance(neighbors, list)
        else (),
        relationship_ids=tuple(str(item) for item in relationships)
        if isinstance(relationships, list)
        else (),
        document_id=str(data["document_id"]) if data.get("document_id") else None,
        lifecycle_state=(
            str(data["lifecycle_state"]) if data.get("lifecycle_state") else None
        ),
    )


def _bundle_to_persisted(
    bundle: W7IndexBundle,
    *,
    embedding_model: EmbeddingModelIdentity,
    embedding_backend: object | None = None,
) -> PersistedIndexBundle:
    from knowledge.embeddings.protocol import EmbeddingBackend
    from knowledge.embeddings.service import EmbeddingService

    compatibility: dict[str, str] = {}

    if embedding_backend is not None and isinstance(embedding_backend, EmbeddingBackend):
        metadata = EmbeddingService(embedding_backend).metadata()
        compatibility = {
            "schema_version": metadata.schema_version,
            "index_version": metadata.index_version,
            "embedding_backend": metadata.embedding_backend,
            "embedding_configuration_hash": metadata.embedding_configuration_hash,
            "corpus_version": metadata.corpus_version,
        }

    return PersistedIndexBundle(
        format_version=INDEX_BUNDLE_FORMAT_VERSION,
        source_digest=bundle.source_digest,
        embedding_model=embedding_model,
        lifecycle_state=bundle.lifecycle_state,
        lexical_entries=tuple(
            entry.to_mapping() for entry in bundle.lexical_index.entries()
        ),
        semantic_entries=tuple(
            entry.to_mapping() for entry in bundle.semantic_index.entries()
        ),
        vector_records=tuple(
            {
                "record_id": record.record_id,
                "target_id": record.target_id,
                "target_type": record.target_type,
                "vector": list(record.vector),
                "document_id": record.document_id,
                "lifecycle_state": record.lifecycle_state,
            }
            for record in bundle.vector_index.records()
        ),
        graph_adjacency=tuple(
            {
                "node_id": item.node_id,
                "node_type": item.node_type,
                "neighbor_ids": list(item.neighbor_ids),
                "relationship_ids": list(item.relationship_ids),
                "document_id": item.document_id,
                "lifecycle_state": item.lifecycle_state,
            }
            for item in bundle.graph_index.adjacency()
        ),
        schema_version=compatibility.get("schema_version", "1.0.0"),
        index_version=compatibility.get("index_version", "1.0.0"),
        embedding_backend=compatibility.get("embedding_backend"),
        embedding_configuration_hash=compatibility.get("embedding_configuration_hash"),
        corpus_version=compatibility.get("corpus_version", "1.0.0"),
    )


def _bundle_from_persisted(persisted: PersistedIndexBundle) -> W7IndexBundle:
    from knowledge.indexing.builder import KnowledgeIndexBundle

    lexical = InMemoryLexicalIndex(
        index_id="lexical-persisted",
        source_digest=persisted.source_digest,
        entries=[_entry_from_mapping(item) for item in persisted.lexical_entries],
    )
    semantic = InMemorySemanticIndex(
        index_id="semantic-persisted",
        source_digest=persisted.source_digest,
        entries=[_entry_from_mapping(item) for item in persisted.semantic_entries],
    )

    lexical_semantic = KnowledgeIndexBundle(
        source_digest=persisted.source_digest,
        lexical_index=lexical,
        semantic_index=semantic,
        lifecycle_state=persisted.lifecycle_state,
    )

    vector_index = InMemoryVectorIndex(
        index_id="vector-persisted",
        source_digest=persisted.source_digest,
        records=[_vector_from_mapping(item) for item in persisted.vector_records],
    )
    graph_index = InMemoryGraphIndex(
        index_id="graph-persisted",
        source_digest=persisted.source_digest,
        adjacency_records=[
            _adjacency_from_mapping(item) for item in persisted.graph_adjacency
        ],
    )

    return W7IndexBundle(
        source_digest=persisted.source_digest,
        lexical_semantic_bundle=lexical_semantic,
        vector_index=vector_index,
        graph_index=graph_index,
        lifecycle_state=persisted.lifecycle_state,
    )


class IndexLifecycleManager:
    """Manage BUILD/LOAD/VALIDATE/INVALIDATE/REBUILD for W7 index bundles."""

    def __init__(
        self,
        *,
        indexes_dir: str | Path,
        embedding_model: EmbeddingModelIdentity,
        vector_dimension: int = 8,
        embedding_backend: object | None = None,
    ) -> None:
        self._indexes_dir = Path(indexes_dir)
        self._indexes_dir.mkdir(parents=True, exist_ok=True)
        self._embedding_model = embedding_model
        self._vector_dimension = vector_dimension
        self._embedding_backend = embedding_backend
        self._builder = W7IndexBuilder(vector_dimension=vector_dimension)
        self._bundle_path = self._indexes_dir / "w7_index_bundle.json"
        self._lifecycle_state = IndexLifecycleState.MISSING

    @property
    def lifecycle_state(self) -> IndexLifecycleState:
        return self._lifecycle_state

    def build(
        self,
        store: GraphStore,
        *,
        embedding_backend: object | None = None,
    ) -> W7IndexBundle:
        """Build and persist a fresh W7 index bundle."""

        backend = embedding_backend if embedding_backend is not None else self._embedding_backend

        if backend is not None:
            from knowledge.production.neural_index_builder import (
                build_production_index_bundle,
            )

            bundle = build_production_index_bundle(store, backend)  # type: ignore[arg-type]
        else:
            bundle = self._builder.build(store)

        persisted = _bundle_to_persisted(
            bundle,
            embedding_model=self._embedding_model,
            embedding_backend=backend,
        )
        self._write_persisted(persisted)
        self._lifecycle_state = IndexLifecycleState.VALID
        return bundle

    def load(self, store: GraphStore) -> W7IndexBundle:
        """Load a persisted bundle or rebuild when missing/stale."""

        if not self._bundle_path.is_file():
            return self.rebuild(store)

        persisted = self._read_persisted()
        self.validate(store, persisted=persisted)
        self._lifecycle_state = IndexLifecycleState.VALID
        return _bundle_from_persisted(persisted)

    def validate(
        self,
        store: GraphStore,
        *,
        persisted: PersistedIndexBundle | None = None,
    ) -> None:
        """Validate persisted bundle compatibility and freshness."""

        active = persisted or self._read_persisted()

        if active.format_version != INDEX_BUNDLE_FORMAT_VERSION:
            raise SchemaMismatchError(
                f"Unsupported index bundle format '{active.format_version}'.",
            )

        if active.embedding_model.fingerprint() != self._embedding_model.fingerprint():
            raise SchemaMismatchError(
                "Persisted embedding model does not match configured model.",
            )

        if (
            active.embedding_configuration_hash is not None
            and self._embedding_backend is not None
        ):
            from knowledge.embeddings.protocol import EmbeddingBackend
            from knowledge.embeddings.service import EmbeddingService

            if isinstance(self._embedding_backend, EmbeddingBackend):
                expected_hash = EmbeddingService(self._embedding_backend).metadata().embedding_configuration_hash

                if active.embedding_configuration_hash != expected_hash:
                    raise SchemaMismatchError(
                        "Persisted embedding configuration hash does not match backend.",
                    )

        current_digest = canonical_graph_record_digest(store.snapshot())

        if active.source_digest != current_digest:
            raise IndexStaleError(
                "Persisted indexes are stale relative to authoritative graph knowledge.",
            )

        if active.lifecycle_state is IndexLifecycleState.INVALID:
            raise IndexStaleError("Persisted indexes are marked INVALID.")

        for record in active.vector_records:
            vector_raw = record.get("vector", [])

            if not isinstance(vector_raw, list):
                raise CorruptionError("Vector record is corrupted.")

            if len(vector_raw) != self._embedding_model.dimension:
                raise IndexValidationError(
                    "Persisted vector dimension does not match embedding model.",
                )

    def invalidate(self) -> None:
        """Mark persisted indexes as stale without deleting artifacts."""

        if not self._bundle_path.is_file():
            self._lifecycle_state = IndexLifecycleState.MISSING
            return

        persisted = self._read_persisted()
        invalidated = PersistedIndexBundle(
            format_version=persisted.format_version,
            source_digest=persisted.source_digest,
            embedding_model=persisted.embedding_model,
            lifecycle_state=IndexLifecycleState.STALE,
            lexical_entries=persisted.lexical_entries,
            semantic_entries=persisted.semantic_entries,
            vector_records=persisted.vector_records,
            graph_adjacency=persisted.graph_adjacency,
            schema_version=persisted.schema_version,
            index_version=persisted.index_version,
            embedding_backend=persisted.embedding_backend,
            embedding_configuration_hash=persisted.embedding_configuration_hash,
            corpus_version=persisted.corpus_version,
        )
        self._write_persisted(invalidated)
        self._lifecycle_state = IndexLifecycleState.STALE

    def rebuild(self, store: GraphStore) -> W7IndexBundle:
        """Rebuild indexes from authoritative graph state."""

        return self.build(store, embedding_backend=self._embedding_backend)

    def _read_persisted(self) -> PersistedIndexBundle:
        payload = json.loads(self._bundle_path.read_text(encoding="utf-8"))

        if not isinstance(payload, dict):
            raise CorruptionError("Index bundle file is corrupted.")

        return PersistedIndexBundle.from_mapping(payload)

    def _write_persisted(self, persisted: PersistedIndexBundle) -> None:
        encoded = json.dumps(persisted.to_mapping(), indent=2, sort_keys=True)
        self._bundle_path.write_text(f"{encoded}\n", encoding="utf-8")
