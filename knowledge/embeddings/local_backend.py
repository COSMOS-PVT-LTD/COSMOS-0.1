"""Deterministic local embedding backend for production offline RAG (Step 7)."""

from __future__ import annotations

import hashlib
import math
from dataclasses import dataclass

from knowledge.embeddings.identity import EmbeddingModelIdentity
from knowledge.indexing.exceptions import IndexValidationError
from knowledge.indexing.w7.vector import validate_vector_components

__all__ = (
    "DeterministicLocalEmbeddingBackend",
    "LocalEmbeddingBackend",
)


@dataclass(frozen=True, slots=True, kw_only=True)
class LocalEmbeddingBackend:
    """Configuration for a local deterministic embedding backend."""

    identity: EmbeddingModelIdentity

    def embed_text(self, text: str) -> tuple[float, ...]:
        """Embed arbitrary text deterministically without network access."""

        if not isinstance(text, str):
            raise IndexValidationError("text must be a string.")

        normalized = " ".join(text.strip().lower().split())

        if not normalized:
            raise IndexValidationError("text must not be blank.")

        digest = hashlib.sha256(
            f"{self.identity.model_id}:{self.identity.model_version}:{normalized}".encode(
                "utf-8",
            ),
        ).digest()
        components: list[float] = []

        for index in range(self.identity.dimension):
            byte_value = digest[index % len(digest)]
            magnitude = (byte_value / 255.0) * 2.0 - 1.0
            components.append(magnitude)

        vector = tuple(components)
        norm = math.sqrt(sum(component * component for component in vector))

        if norm == 0.0:
            return vector

        return tuple(component / norm for component in vector)


class DeterministicLocalEmbeddingBackend(LocalEmbeddingBackend):
    """Default COSMOS local embedding backend — offline, reproducible, no downloads."""

    def __init__(
        self,
        *,
        dimension: int = 8,
        model_id: str = "cosmos-local-deterministic-v1",
        model_version: str = "1.0.0",
    ) -> None:
        if dimension <= 0:
            raise IndexValidationError("dimension must be positive.")

        super().__init__(
            identity=EmbeddingModelIdentity(
                model_id=model_id,
                model_version=model_version,
                dimension=dimension,
                provider="local-deterministic",
                requires_network=False,
            ),
        )

    def embed_query(self, query_text: str) -> tuple[float, ...]:
        """Embed a retrieval query vector."""

        return validate_vector_components(self.embed_text(query_text))

    def embed_document(self, document_text: str) -> tuple[float, ...]:
        """Embed a document text span."""

        return validate_vector_components(self.embed_text(document_text))

    def embed_batch(self, texts: tuple[str, ...]) -> tuple[tuple[float, ...], ...]:
        return tuple(self.embed_text(text) for text in texts)
