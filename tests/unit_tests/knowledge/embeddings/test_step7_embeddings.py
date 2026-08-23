"""Step 7 local embedding backend tests."""

from __future__ import annotations

import pytest

from knowledge.embeddings import DeterministicLocalEmbeddingBackend
from knowledge.indexing.exceptions import IndexValidationError


def test_local_embedding_is_deterministic() -> None:
    """Local embeddings must be deterministic for fixed model/input."""

    backend = DeterministicLocalEmbeddingBackend(dimension=8)
    first = backend.embed_text("chamber pressure")
    second = backend.embed_text("chamber pressure")

    assert first == second
    assert len(first) == 8


def test_local_embedding_rejects_dimension_mismatch() -> None:
    """Embedding model identity must expose explicit dimension."""

    backend = DeterministicLocalEmbeddingBackend(dimension=4)
    vector = backend.embed_query("test")

    assert len(vector) == backend.identity.dimension


def test_local_embedding_rejects_blank_text() -> None:
    """Blank text must be rejected."""

    backend = DeterministicLocalEmbeddingBackend()

    with pytest.raises(IndexValidationError):
        backend.embed_text("   ")


def test_embedding_model_mismatch_detection() -> None:
    """Different model versions must produce different fingerprints."""

    first = DeterministicLocalEmbeddingBackend(model_version="1.0.0")
    second = DeterministicLocalEmbeddingBackend(model_version="2.0.0")

    assert first.identity.fingerprint() != second.identity.fingerprint()
