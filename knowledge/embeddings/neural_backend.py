"""Local neural embedding backend — offline MLP inference, no cloud dependency."""

from __future__ import annotations

import hashlib

from knowledge.embeddings.feature_encoder import FeatureEncoder
from knowledge.embeddings.identity import EmbeddingModelIdentity
from knowledge.embeddings.mlp import MLPWeights, mlp_forward, seeded_mlp_weights
from knowledge.indexing.exceptions import IndexValidationError
from knowledge.indexing.w7.vector import validate_vector_components

__all__ = (
    "DEFAULT_NEURAL_DIMENSION",
    "DEFAULT_NEURAL_MODEL_ID",
    "DEFAULT_NEURAL_MODEL_VERSION",
    "LocalNeuralEmbeddingBackend",
)


DEFAULT_NEURAL_MODEL_ID = "cosmos-local-neural-mini-v1"
DEFAULT_NEURAL_MODEL_VERSION = "1.0.0"
DEFAULT_NEURAL_DIMENSION = 64
_FEATURE_DIMENSION = 512
_HIDDEN_DIMENSION = 128


class LocalNeuralEmbeddingBackend:
    """Local neural embedding backend using a seeded MLP over engineering features."""

    def __init__(
        self,
        *,
        model_id: str = DEFAULT_NEURAL_MODEL_ID,
        model_version: str = DEFAULT_NEURAL_MODEL_VERSION,
        dimension: int = DEFAULT_NEURAL_DIMENSION,
    ) -> None:
        if dimension <= 0:
            raise IndexValidationError("dimension must be positive.")

        self._identity = EmbeddingModelIdentity(
            model_id=model_id,
            model_version=model_version,
            dimension=dimension,
            provider="local-neural-mlp",
            requires_network=False,
        )
        self._encoder = FeatureEncoder(feature_dimension=_FEATURE_DIMENSION)
        self._weights = seeded_mlp_weights(
            seed=f"{model_id}@{model_version}",
            input_dim=_FEATURE_DIMENSION,
            hidden_dim=_HIDDEN_DIMENSION,
            output_dim=dimension,
        )

    @property
    def identity(self) -> EmbeddingModelIdentity:
        return self._identity

    @property
    def weights(self) -> MLPWeights:
        return self._weights

    def configuration_hash(self) -> str:
        """Return a stable hash of model configuration for index compatibility."""

        payload = (
            f"{self._identity.fingerprint()}:"
            f"{_FEATURE_DIMENSION}:{_HIDDEN_DIMENSION}:"
            f"{self._weights.w1[0][0]}"
        )
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()

    def embed_text(self, text: str) -> tuple[float, ...]:
        if not isinstance(text, str):
            raise IndexValidationError("text must be a string.")

        normalized = " ".join(text.strip().lower().split())

        if not normalized:
            raise IndexValidationError("text must not be blank.")

        features = self._encoder.encode(normalized)
        return mlp_forward(features, self._weights)

    def embed_query(self, query_text: str) -> tuple[float, ...]:
        return validate_vector_components(self.embed_text(query_text))

    def embed_document(self, document_text: str) -> tuple[float, ...]:
        return validate_vector_components(self.embed_text(document_text))

    def embed_batch(self, texts: tuple[str, ...]) -> tuple[tuple[float, ...], ...]:
        return tuple(self.embed_text(text) for text in texts)
