"""
COSMOS Knowledge Foundation

Module:
    knowledge.source.vault

Purpose:
    Source-vault abstraction for controlled artifact storage (NEW KG-008).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from knowledge.source.exceptions import (
    IntegrityMismatchError,
    IntegrityValidationError,
    VaultNotFoundError,
    VaultValidationError,
)
from knowledge.source.integrity import IntegrityService, verify_digest

__all__ = (
    "InMemorySourceVault",
    "SourceVault",
    "VaultArtifact",
    "VaultArtifactMetadata",
)


def _validate_non_empty_string(field_name: str, value: str) -> str:
    if not isinstance(value, str):
        raise VaultValidationError(f"{field_name} must be a string.")

    cleaned = value.strip()

    if not cleaned:
        raise VaultValidationError(f"{field_name} must not be blank.")

    return cleaned


@dataclass(frozen=True, slots=True, kw_only=True)
class VaultArtifactMetadata:
    """Non-content metadata stored with a vault artifact."""

    source_format: str | None = None
    media_type: str | None = None
    license_metadata: dict[str, object] | None = None

    def to_mapping(self) -> dict[str, object]:
        payload: dict[str, object] = {}

        if self.source_format is not None:
            payload["source_format"] = self.source_format
        if self.media_type is not None:
            payload["media_type"] = self.media_type
        if self.license_metadata is not None:
            payload["license_metadata"] = self.license_metadata

        return payload


@dataclass(frozen=True, slots=True, kw_only=True)
class VaultArtifact:
    """Stored source artifact with deterministic content addressing."""

    source_id: str
    artifact_id: str
    content: bytes
    content_hash: str
    metadata: VaultArtifactMetadata = VaultArtifactMetadata()

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "source_id",
            _validate_non_empty_string("source_id", self.source_id),
        )
        object.__setattr__(
            self,
            "artifact_id",
            _validate_non_empty_string("artifact_id", self.artifact_id),
        )

        if not isinstance(self.content, bytes):
            raise VaultValidationError("content must be bytes.")

        object.__setattr__(
            self,
            "content_hash",
            _validate_non_empty_string("content_hash", self.content_hash),
        )

        if not isinstance(self.metadata, VaultArtifactMetadata):
            raise VaultValidationError(
                "metadata must be a VaultArtifactMetadata instance."
            )

    @property
    def vault_key(self) -> tuple[str, str]:
        """Return the deterministic vault addressing key."""

        return (self.source_id, self.artifact_id)


class SourceVault(Protocol):
    """Backend-neutral source vault contract."""

    def store(self, artifact: VaultArtifact) -> VaultArtifact:
        """Store an artifact. Raises when the key already exists."""

    def retrieve(self, source_id: str, artifact_id: str) -> VaultArtifact:
        """Retrieve a stored artifact."""

    def exists(self, source_id: str, artifact_id: str) -> bool:
        """Return True when an artifact exists."""

    def delete(self, source_id: str, artifact_id: str) -> None:
        """Delete a stored artifact."""

    def verify_integrity(self, source_id: str, artifact_id: str) -> bool:
        """Return True when stored content matches its recorded digest."""


class InMemorySourceVault:
    """Reference in-memory source vault implementation."""

    def __init__(self, integrity: IntegrityService | None = None) -> None:
        self._integrity = integrity or IntegrityService()
        self._artifacts: dict[tuple[str, str], VaultArtifact] = {}

    def store(self, artifact: VaultArtifact) -> VaultArtifact:
        if not isinstance(artifact, VaultArtifact):
            raise VaultValidationError(
                "artifact must be a VaultArtifact instance."
            )

        verify_digest(artifact.content, artifact.content_hash)
        key = artifact.vault_key

        if key in self._artifacts:
            raise VaultValidationError(
                f"Vault artifact '{artifact.artifact_id}' already exists "
                f"for source '{artifact.source_id}'."
            )

        self._artifacts[key] = artifact
        return artifact

    def retrieve(self, source_id: str, artifact_id: str) -> VaultArtifact:
        key = (
            _validate_non_empty_string("source_id", source_id),
            _validate_non_empty_string("artifact_id", artifact_id),
        )

        try:
            return self._artifacts[key]
        except KeyError as exc:
            raise VaultNotFoundError(
                f"Vault artifact '{artifact_id}' was not found for "
                f"source '{source_id}'."
            ) from exc

    def exists(self, source_id: str, artifact_id: str) -> bool:
        key = (
            _validate_non_empty_string("source_id", source_id),
            _validate_non_empty_string("artifact_id", artifact_id),
        )

        return key in self._artifacts

    def delete(self, source_id: str, artifact_id: str) -> None:
        key = (
            _validate_non_empty_string("source_id", source_id),
            _validate_non_empty_string("artifact_id", artifact_id),
        )

        if key not in self._artifacts:
            raise VaultNotFoundError(
                f"Vault artifact '{artifact_id}' was not found for "
                f"source '{source_id}'."
            )

        del self._artifacts[key]

    def verify_integrity(self, source_id: str, artifact_id: str) -> bool:
        artifact = self.retrieve(source_id, artifact_id)

        try:
            verify_digest(artifact.content, artifact.content_hash)
        except (IntegrityMismatchError, IntegrityValidationError):
            return False

        return True
