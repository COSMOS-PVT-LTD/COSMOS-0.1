"""Embedding model identity contracts for production local RAG."""

from __future__ import annotations

from dataclasses import dataclass

from knowledge.indexing.exceptions import IndexValidationError

__all__ = ("EmbeddingModelIdentity",)


def _validate_non_empty(field_name: str, value: str) -> str:
    cleaned = value.strip()

    if not cleaned:
        raise IndexValidationError(f"{field_name} must not be blank.")

    return cleaned


@dataclass(frozen=True, slots=True, kw_only=True)
class EmbeddingModelIdentity:
    """Identity metadata for a local embedding model/backend."""

    model_id: str
    model_version: str
    dimension: int
    provider: str = "local-deterministic"
    requires_network: bool = False

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "model_id",
            _validate_non_empty("model_id", self.model_id),
        )
        object.__setattr__(
            self,
            "model_version",
            _validate_non_empty("model_version", self.model_version),
        )
        object.__setattr__(
            self,
            "provider",
            _validate_non_empty("provider", self.provider),
        )

        if not isinstance(self.dimension, int) or isinstance(self.dimension, bool):
            raise IndexValidationError("dimension must be an integer.")

        if self.dimension <= 0:
            raise IndexValidationError("dimension must be positive.")

    def to_mapping(self) -> dict[str, object]:
        return {
            "dimension": self.dimension,
            "model_id": self.model_id,
            "model_version": self.model_version,
            "provider": self.provider,
            "requires_network": self.requires_network,
        }

    @classmethod
    def from_mapping(cls, data: dict[str, object]) -> EmbeddingModelIdentity:
        dimension_raw = data["dimension"]
        if not isinstance(dimension_raw, int) or isinstance(dimension_raw, bool):
            raise IndexValidationError("dimension must be an integer.")

        return cls(
            model_id=str(data["model_id"]),
            model_version=str(data["model_version"]),
            dimension=dimension_raw,
            provider=str(data.get("provider", "local-deterministic")),
            requires_network=bool(data.get("requires_network", False)),
        )

    def fingerprint(self) -> str:
        """Return a stable fingerprint for compatibility checks."""

        return f"{self.model_id}@{self.model_version}:{self.dimension}"
