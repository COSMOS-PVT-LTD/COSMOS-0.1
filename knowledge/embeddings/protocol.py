"""Embedding backend protocol for COSMOS local RAG."""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from knowledge.embeddings.identity import EmbeddingModelIdentity

__all__ = ("EmbeddingBackend",)


@runtime_checkable
class EmbeddingBackend(Protocol):
    """Protocol for local embedding backends (deterministic or neural)."""

    @property
    def identity(self) -> EmbeddingModelIdentity: ...

    def embed_query(self, query_text: str) -> tuple[float, ...]: ...

    def embed_document(self, document_text: str) -> tuple[float, ...]: ...

    def embed_batch(self, texts: tuple[str, ...]) -> tuple[tuple[float, ...], ...]:
        """Embed a batch of texts."""
