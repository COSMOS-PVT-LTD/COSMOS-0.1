"""Vector index for KG-034 (W7)."""

from __future__ import annotations

import hashlib
import math
from collections.abc import Sequence
from dataclasses import dataclass
from typing import Protocol

from knowledge.graph.repository import GraphStore
from knowledge.graph.serialization import canonical_graph_record_digest
from knowledge.indexing.exceptions import IndexStaleError, IndexValidationError
from knowledge.indexing.models import IndexLifecycleState, IndexMetadata, IndexStatistics

__all__ = (
    "InMemoryVectorIndex",
    "VectorIndex",
    "VectorRecord",
    "build_vector_index_from_records",
    "cosine_similarity",
    "require_fresh_vector_index",
    "validate_vector_components",
)


def validate_vector_components(vector: tuple[float, ...]) -> tuple[float, ...]:
    """Validate vector components are finite numbers."""

    if not isinstance(vector, tuple):
        raise IndexValidationError("vector must be a tuple.")

    if not vector:
        raise IndexValidationError("vector must not be empty.")

    validated: list[float] = []

    for index, component in enumerate(vector):
        if not isinstance(component, (int, float)) or isinstance(component, bool):
            raise IndexValidationError(
                f"vector component at index {index} must be a number.",
            )

        value = float(component)

        if not math.isfinite(value):
            raise IndexValidationError(
                f"vector component at index {index} must be finite.",
            )

        validated.append(value)

    return tuple(validated)


def cosine_similarity(
    left: tuple[float, ...],
    right: tuple[float, ...],
) -> float:
    """Return cosine similarity between two vectors."""

    left_valid = validate_vector_components(left)
    right_valid = validate_vector_components(right)

    if len(left_valid) != len(right_valid):
        raise IndexValidationError("vector dimensions must match for similarity.")

    dot = sum(left_component * right_component for left_component, right_component in zip(left_valid, right_valid, strict=True))
    left_norm = math.sqrt(sum(component * component for component in left_valid))
    right_norm = math.sqrt(sum(component * component for component in right_valid))

    if left_norm == 0.0 or right_norm == 0.0:
        return 0.0

    return dot / (left_norm * right_norm)


@dataclass(frozen=True, slots=True, kw_only=True)
class VectorRecord:
    """Single vector-index record referencing authoritative knowledge."""

    record_id: str
    target_id: str
    target_type: str
    vector: tuple[float, ...]
    document_id: str | None = None
    lifecycle_state: str | None = None

    def __post_init__(self) -> None:
        if not self.record_id.strip():
            raise IndexValidationError("record_id must not be blank.")

        if not self.target_id.strip():
            raise IndexValidationError("target_id must not be blank.")

        if not self.target_type.strip():
            raise IndexValidationError("target_type must not be blank.")

        object.__setattr__(
            self,
            "vector",
            validate_vector_components(self.vector),
        )


class VectorIndex(Protocol):
    """Backend-neutral vector index contract."""

    def metadata(self) -> IndexMetadata:
        """Return index metadata."""

    def statistics(self) -> IndexStatistics:
        """Return aggregate index statistics."""

    def records(self) -> tuple[VectorRecord, ...]:
        """Return all vector records in deterministic order."""

    def dimension(self) -> int:
        """Return vector dimensionality."""

    def similarity(
        self,
        query_vector: tuple[float, ...],
        *,
        limit: int,
    ) -> tuple[tuple[VectorRecord, float], ...]:
        """Return ranked vector matches with deterministic tie-breaking."""

    def is_stale(self, source_digest: str) -> bool:
        """Return True when the index is stale relative to source knowledge."""


class InMemoryVectorIndex:
    """Reference in-memory vector index using caller-supplied vectors."""

    def __init__(
        self,
        *,
        index_id: str,
        source_digest: str,
        records: Sequence[VectorRecord],
    ) -> None:
        self._index_id = index_id.strip()
        self._source_digest = source_digest.strip()
        sorted_records = tuple(sorted(records, key=lambda item: item.record_id))
        seen_record_ids: set[str] = set()
        dimension: int | None = None

        for record in sorted_records:
            if record.record_id in seen_record_ids:
                raise IndexValidationError(
                    f"Duplicate vector record_id '{record.record_id}'.",
                )

            seen_record_ids.add(record.record_id)

            if dimension is None:
                dimension = len(record.vector)
            elif len(record.vector) != dimension:
                raise IndexValidationError(
                    "All vector records must share the same dimension.",
                )

        self._records = sorted_records
        self._dimension = dimension or 0
        self._records_by_id = {
            record.record_id: record for record in self._records
        }

    def metadata(self) -> IndexMetadata:
        return IndexMetadata(
            index_id=self._index_id,
            source_digest=self._source_digest,
            entry_count=len(self._records),
            lifecycle_state=IndexLifecycleState.VALID,
        )

    def statistics(self) -> IndexStatistics:
        target_ids = {record.target_id for record in self._records}

        return IndexStatistics(
            entry_count=len(self._records),
            unique_term_count=self._dimension,
            target_count=len(target_ids),
        )

    def records(self) -> tuple[VectorRecord, ...]:
        return self._records

    def dimension(self) -> int:
        return self._dimension

    def similarity(
        self,
        query_vector: tuple[float, ...],
        *,
        limit: int,
    ) -> tuple[tuple[VectorRecord, float], ...]:
        if not isinstance(limit, int) or isinstance(limit, bool):
            raise IndexValidationError("limit must be an integer.")

        if limit < 0:
            raise IndexValidationError("limit must be non-negative.")

        if limit == 0 or not self._records or self._dimension == 0:
            return ()

        validated_query = validate_vector_components(query_vector)

        if len(validated_query) != self._dimension:
            raise IndexValidationError(
                "query vector dimension does not match index dimension.",
            )

        scored = [
            (record, cosine_similarity(validated_query, record.vector))
            for record in self._records
        ]

        filtered = [
            (record, score)
            for record, score in scored
            if score > 0.0
        ]

        ranked = sorted(
            filtered,
            key=lambda item: (-item[1], item[0].record_id),
        )

        return tuple(ranked[:limit])

    def is_stale(self, source_digest: str) -> bool:
        return self._source_digest != source_digest.strip()


def build_vector_index_from_records(
    *,
    index_id: str,
    source_digest: str,
    records: Sequence[VectorRecord],
) -> InMemoryVectorIndex:
    """Build a vector index from caller-supplied vector records."""

    return InMemoryVectorIndex(
        index_id=index_id,
        source_digest=source_digest,
        records=records,
    )


def deterministic_reference_vector(
    *,
    target_id: str,
    dimension: int,
) -> tuple[float, ...]:
    """
    Build a deterministic reference vector from a target identifier.

  This is a test/reference helper — not an embedding model.
    """

    if dimension <= 0:
        raise IndexValidationError("dimension must be positive.")

    digest = hashlib.sha256(target_id.encode("utf-8")).digest()
    components: list[float] = []

    for index in range(dimension):
        byte_value = digest[index % len(digest)]
        components.append((byte_value / 255.0) * 2.0 - 1.0)

    return tuple(components)


def build_reference_vector_index_from_store(
    store: GraphStore,
    *,
    index_id: str = "vector-default",
    dimension: int = 8,
) -> InMemoryVectorIndex:
    """Build a reference vector index using deterministic target-derived vectors."""

    record = store.snapshot()
    source_digest = canonical_graph_record_digest(record)
    records: list[VectorRecord] = []

    for node in sorted(record.nodes, key=lambda item: item.node_id):
        lifecycle_value = node.properties.get("lifecycle_state")
        document_id = node.properties.get("document_id")

        records.append(
            VectorRecord(
                record_id=f"vec:{node.node_id}",
                target_id=node.node_id,
                target_type=node.node_type,
                vector=deterministic_reference_vector(
                    target_id=node.node_id,
                    dimension=dimension,
                ),
                document_id=str(document_id)
                if isinstance(document_id, str)
                else None,
                lifecycle_state=str(lifecycle_value)
                if lifecycle_value is not None
                else None,
            ),
        )

    return build_vector_index_from_records(
        index_id=index_id,
        source_digest=source_digest,
        records=records,
    )


def require_fresh_vector_index(
    index: VectorIndex,
    source_digest: str,
) -> None:
    """Raise when the vector index is stale."""

    if index.is_stale(source_digest):
        raise IndexStaleError(
            "Vector index is stale relative to authoritative knowledge.",
        )
