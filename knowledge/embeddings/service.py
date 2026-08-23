"""Embedding service with batching and compatibility metadata."""

from __future__ import annotations

from dataclasses import dataclass

from knowledge.embeddings.neural_backend import LocalNeuralEmbeddingBackend
from knowledge.embeddings.local_backend import DeterministicLocalEmbeddingBackend
from knowledge.embeddings.protocol import EmbeddingBackend
from knowledge.indexing.exceptions import IndexValidationError

__all__ = (
    "EmbeddingService",
    "EmbeddingServiceMetadata",
    "create_embedding_backend",
)


@dataclass(frozen=True, slots=True, kw_only=True)
class EmbeddingServiceMetadata:
    """Persisted embedding/index compatibility metadata."""

    schema_version: str
    index_version: str
    embedding_backend: str
    embedding_model_id: str
    embedding_model_version: str
    embedding_dimension: int
    embedding_configuration_hash: str
    corpus_version: str = "1.0.0"

    def to_mapping(self) -> dict[str, object]:
        return {
            "corpus_version": self.corpus_version,
            "embedding_backend": self.embedding_backend,
            "embedding_configuration_hash": self.embedding_configuration_hash,
            "embedding_dimension": self.embedding_dimension,
            "embedding_model_id": self.embedding_model_id,
            "embedding_model_version": self.embedding_model_version,
            "index_version": self.index_version,
            "schema_version": self.schema_version,
        }


class EmbeddingService:
    """Batch-capable embedding service wrapper."""

    def __init__(self, backend: EmbeddingBackend) -> None:
        self._backend = backend

    @property
    def backend(self) -> EmbeddingBackend:
        return self._backend

    def embed_documents(self, texts: tuple[str, ...]) -> tuple[tuple[float, ...], ...]:
        return self._backend.embed_batch(texts)

    def metadata(self, *, schema_version: str = "1.0.0", index_version: str = "1.0.0") -> EmbeddingServiceMetadata:
        identity = self._backend.identity
        config_hash = identity.fingerprint()

        if isinstance(self._backend, LocalNeuralEmbeddingBackend):
            config_hash = self._backend.configuration_hash()

        return EmbeddingServiceMetadata(
            schema_version=schema_version,
            index_version=index_version,
            embedding_backend=identity.provider,
            embedding_model_id=identity.model_id,
            embedding_model_version=identity.model_version,
            embedding_dimension=identity.dimension,
            embedding_configuration_hash=config_hash,
        )

    def validate_dimension(self, vector: tuple[float, ...]) -> None:
        if len(vector) != self._backend.identity.dimension:
            raise IndexValidationError(
                f"Vector dimension {len(vector)} does not match "
                f"backend dimension {self._backend.identity.dimension}.",
            )


def create_embedding_backend(mode: str = "deterministic") -> EmbeddingBackend:
    """Factory for supported local embedding backends."""

    normalized = mode.strip().lower()

    if normalized in {"deterministic", "deterministic-v1", "v1"}:
        return DeterministicLocalEmbeddingBackend()

    if normalized in {"neural", "neural-v1", "local-neural"}:
        return LocalNeuralEmbeddingBackend()

    raise IndexValidationError(f"Unsupported embedding backend mode '{mode}'.")
