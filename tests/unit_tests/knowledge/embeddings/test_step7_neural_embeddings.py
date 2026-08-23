"""Neural embedding backend tests (Step 7 final completion)."""

from __future__ import annotations

import pytest

from knowledge.embeddings import (
    DeterministicLocalEmbeddingBackend,
    LocalNeuralEmbeddingBackend,
    create_embedding_backend,
)
from knowledge.embeddings.service import EmbeddingService
from knowledge.indexing.exceptions import IndexValidationError


def test_neural_embedding_is_deterministic() -> None:
    backend = LocalNeuralEmbeddingBackend()
    first = backend.embed_query("liquid oxygen oxidizer")
    second = backend.embed_query("liquid oxygen oxidizer")

    assert first == second
    assert len(first) == backend.identity.dimension


def test_neural_embedding_dimension_and_normalization() -> None:
    backend = LocalNeuralEmbeddingBackend(dimension=64)
    vector = backend.embed_document("chamber pressure instability")

    assert len(vector) == 64
    norm = sum(component * component for component in vector) ** 0.5
    assert 0.99 <= norm <= 1.01


def test_neural_embed_batch_matches_single() -> None:
    backend = LocalNeuralEmbeddingBackend()
    texts = ("LOX feed line", "turbopump cavitation")
    batch = backend.embed_batch(texts)

    assert batch == (backend.embed_text(texts[0]), backend.embed_text(texts[1]))


def test_create_embedding_backend_modes() -> None:
    deterministic = create_embedding_backend("deterministic")
    neural = create_embedding_backend("neural")

    assert deterministic.identity.provider == "local-deterministic"
    assert neural.identity.provider == "local-neural-mlp"
    assert deterministic.identity.dimension != neural.identity.dimension


def test_embedding_service_metadata_includes_configuration_hash() -> None:
    backend = LocalNeuralEmbeddingBackend()
    metadata = EmbeddingService(backend).metadata()

    assert metadata.embedding_backend == "local-neural-mlp"
    assert metadata.embedding_model_id == "cosmos-local-neural-mini-v1"
    assert metadata.embedding_configuration_hash
    assert metadata.embedding_dimension == 64


def test_neural_backend_rejects_blank_text() -> None:
    backend = LocalNeuralEmbeddingBackend()

    with pytest.raises(IndexValidationError):
        backend.embed_text("  ")


def test_deterministic_and_neural_produce_different_vectors() -> None:
    deterministic = DeterministicLocalEmbeddingBackend()
    neural = LocalNeuralEmbeddingBackend()
    text = "specific impulse propulsion efficiency"

    assert deterministic.embed_text(text) != neural.embed_text(text)[:8]
