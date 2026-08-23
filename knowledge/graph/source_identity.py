"""
COSMOS Knowledge Foundation

Module:
    knowledge.graph.source_identity

Purpose:
    Deterministic source and artifact identity contracts for the Knowledge Graph.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from enum import Enum

from knowledge.graph.exceptions import GraphValidationError

__all__ = (
    "ArtifactIdentity",
    "SourceIdentity",
    "SourceStatus",
    "SourceType",
    "is_valid_sha256_hex",
)

_SHA256_PATTERN = re.compile(r"^[a-fA-F0-9]{64}$")


def is_valid_sha256_hex(value: str) -> bool:
    """Return True when value is a 64-character hexadecimal SHA-256 digest."""

    return bool(_SHA256_PATTERN.match(value))


def _validate_non_empty_string(field_name: str, value: str) -> str:
    if not isinstance(value, str):
        raise GraphValidationError(f"{field_name} must be a string.")

    cleaned = value.strip()

    if not cleaned:
        raise GraphValidationError(f"{field_name} must not be blank.")

    return cleaned


def _validate_optional_non_empty_string(
    field_name: str,
    value: str | None,
) -> str | None:
    if value is None:
        return None

    return _validate_non_empty_string(field_name, value)


def _validate_optional_sha256(
    field_name: str,
    value: str | None,
) -> str | None:
    if value is None:
        return None

    cleaned = _validate_non_empty_string(field_name, value)

    if not is_valid_sha256_hex(cleaned):
        raise GraphValidationError(
            f"{field_name} must be a 64-character hexadecimal SHA-256 digest."
        )

    return cleaned.lower()


class SourceType(Enum):
    """Discriminator for registered knowledge sources."""

    PDF = "PDF"
    BOOK = "BOOK"
    JOURNAL = "JOURNAL"
    STANDARD = "STANDARD"
    MANUAL = "MANUAL"
    WEBSITE = "WEBSITE"
    GIT_REPOSITORY = "GIT_REPOSITORY"
    DATASET = "DATASET"
    INTERNAL_DOCUMENT = "INTERNAL_DOCUMENT"
    ENGINEERING_NOTE = "ENGINEERING_NOTE"
    OTHER = "OTHER"


class SourceStatus(Enum):
    """Lifecycle status for a registered source."""

    REGISTERED = "REGISTERED"
    VERIFIED = "VERIFIED"
    INGESTING = "INGESTING"
    INGESTED = "INGESTED"
    DEPRECATED = "DEPRECATED"
    ARCHIVED = "ARCHIVED"


@dataclass(frozen=True, slots=True, kw_only=True)
class SourceIdentity:
    """
    Stable identity for a knowledge source.

    Identity is deterministic from explicit field values. Hash fields are
    optional at registration time but must be valid SHA-256 digests when set.
    """

    source_id: str
    source_type: SourceType
    title: str
    version: str | None = None
    content_hash: str | None = None
    file_hash: str | None = None
    origin: str | None = None
    license_identifier: str | None = None
    source_status: SourceStatus = SourceStatus.REGISTERED
    lineage_parent_source_id: str | None = None

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "source_id",
            _validate_non_empty_string("source_id", self.source_id),
        )

        if not isinstance(self.source_type, SourceType):
            raise GraphValidationError("source_type must be a SourceType value.")

        object.__setattr__(
            self,
            "title",
            _validate_non_empty_string("title", self.title),
        )
        object.__setattr__(
            self,
            "version",
            _validate_optional_non_empty_string("version", self.version),
        )
        object.__setattr__(
            self,
            "content_hash",
            _validate_optional_sha256("content_hash", self.content_hash),
        )
        object.__setattr__(
            self,
            "file_hash",
            _validate_optional_sha256("file_hash", self.file_hash),
        )
        object.__setattr__(
            self,
            "origin",
            _validate_optional_non_empty_string("origin", self.origin),
        )
        object.__setattr__(
            self,
            "license_identifier",
            _validate_optional_non_empty_string(
                "license_identifier",
                self.license_identifier,
            ),
        )

        if not isinstance(self.source_status, SourceStatus):
            raise GraphValidationError(
                "source_status must be a SourceStatus value."
            )

        object.__setattr__(
            self,
            "lineage_parent_source_id",
            _validate_optional_non_empty_string(
                "lineage_parent_source_id",
                self.lineage_parent_source_id,
            ),
        )

    def identity_key(self) -> tuple[str, str, str | None]:
        """Return the deterministic identity key for this source."""

        return (self.source_id, self.source_type.value, self.version)

    def to_mapping(self) -> dict[str, object]:
        """Return a serialization-friendly representation."""

        payload: dict[str, object] = {
            "source_id": self.source_id,
            "source_type": self.source_type.value,
            "title": self.title,
            "source_status": self.source_status.value,
        }

        if self.version is not None:
            payload["version"] = self.version
        if self.content_hash is not None:
            payload["content_hash"] = self.content_hash
        if self.file_hash is not None:
            payload["file_hash"] = self.file_hash
        if self.origin is not None:
            payload["origin"] = self.origin
        if self.license_identifier is not None:
            payload["license_identifier"] = self.license_identifier
        if self.lineage_parent_source_id is not None:
            payload["lineage_parent_source_id"] = self.lineage_parent_source_id

        return payload


@dataclass(frozen=True, slots=True, kw_only=True)
class ArtifactIdentity:
    """
    Stable identity for a source artifact such as a file or document revision.

    Artifacts are scoped to a parent ``source_id`` and do not embed artifact
    content.
    """

    artifact_id: str
    source_id: str
    artifact_type: str
    version: str | None = None
    content_hash: str | None = None
    file_hash: str | None = None

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "artifact_id",
            _validate_non_empty_string("artifact_id", self.artifact_id),
        )
        object.__setattr__(
            self,
            "source_id",
            _validate_non_empty_string("source_id", self.source_id),
        )
        object.__setattr__(
            self,
            "artifact_type",
            _validate_non_empty_string("artifact_type", self.artifact_type),
        )
        object.__setattr__(
            self,
            "version",
            _validate_optional_non_empty_string("version", self.version),
        )
        object.__setattr__(
            self,
            "content_hash",
            _validate_optional_sha256("content_hash", self.content_hash),
        )
        object.__setattr__(
            self,
            "file_hash",
            _validate_optional_sha256("file_hash", self.file_hash),
        )

    def identity_key(self) -> tuple[str, str, str | None]:
        """Return the deterministic identity key for this artifact."""

        return (self.artifact_id, self.source_id, self.version)

    def to_mapping(self) -> dict[str, object]:
        """Return a serialization-friendly representation."""

        payload: dict[str, object] = {
            "artifact_id": self.artifact_id,
            "source_id": self.source_id,
            "artifact_type": self.artifact_type,
        }

        if self.version is not None:
            payload["version"] = self.version
        if self.content_hash is not None:
            payload["content_hash"] = self.content_hash
        if self.file_hash is not None:
            payload["file_hash"] = self.file_hash

        return payload
