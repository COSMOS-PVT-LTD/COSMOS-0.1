"""Public exports for knowledge.embeddings."""

from __future__ import annotations

from knowledge.embeddings.identity import EmbeddingModelIdentity
from knowledge.embeddings.local_backend import (
    DeterministicLocalEmbeddingBackend,
    LocalEmbeddingBackend,
)
from knowledge.embeddings.neural_backend import LocalNeuralEmbeddingBackend
from knowledge.embeddings.protocol import EmbeddingBackend
from knowledge.embeddings.service import EmbeddingService, EmbeddingServiceMetadata, create_embedding_backend

__all__ = (
    "DeterministicLocalEmbeddingBackend",
    "EmbeddingBackend",
    "EmbeddingModelIdentity",
    "EmbeddingService",
    "EmbeddingServiceMetadata",
    "LocalEmbeddingBackend",
    "LocalNeuralEmbeddingBackend",
    "create_embedding_backend",
)
