"""Unit tests for knowledge.source (KG-BLOCK-005 W1)."""

from __future__ import annotations

import pytest

from knowledge.source import (
    InMemorySourceVault,
    IntegrityMismatchError,
    IntegrityService,
    IntegrityValidationError,
    LicenseMetadata,
    VaultArtifact,
    VaultNotFoundError,
    VaultValidationError,
    sha256_bytes_digest,
    verify_digest,
)


def test_sha256_digest_is_deterministic() -> None:
    """Same content must produce the same digest."""

    content = b"cosmos-source-content"

    assert sha256_bytes_digest(content) == sha256_bytes_digest(content)
    assert sha256_bytes_digest(content) != sha256_bytes_digest(b"other")


def test_verify_digest_rejects_mismatch() -> None:
    """Integrity verification must fail on digest mismatch."""

    content = b"artifact-bytes"
    digest = sha256_bytes_digest(content)

    verify_digest(content, digest)

    with pytest.raises(IntegrityMismatchError):
        verify_digest(b"changed", digest)


def test_verify_digest_rejects_invalid_format() -> None:
    """Invalid digest strings must be rejected."""

    with pytest.raises(IntegrityValidationError):
        verify_digest(b"data", "not-a-digest")


def test_vault_store_and_retrieve() -> None:
    """Vault must store and retrieve artifacts with integrity."""

    content = b"vault-payload"
    digest = sha256_bytes_digest(content)
    vault = InMemorySourceVault()

    artifact = VaultArtifact(
        source_id="SRC-001",
        artifact_id="ART-001",
        content=content,
        content_hash=digest,
    )

    vault.store(artifact)
    retrieved = vault.retrieve("SRC-001", "ART-001")

    assert retrieved.content == content
    assert vault.verify_integrity("SRC-001", "ART-001")


def test_vault_rejects_duplicate_artifact() -> None:
    """Duplicate vault keys must fail deterministically."""

    vault = InMemorySourceVault()
    digest = sha256_bytes_digest(b"payload")
    artifact = VaultArtifact(
        source_id="SRC-001",
        artifact_id="ART-001",
        content=b"payload",
        content_hash=digest,
    )

    vault.store(artifact)

    with pytest.raises(VaultValidationError):
        vault.store(artifact)


def test_vault_delete_requires_existing_artifact() -> None:
    """Deleting a missing artifact must raise VaultNotFoundError."""

    vault = InMemorySourceVault()

    with pytest.raises(VaultNotFoundError):
        vault.delete("SRC-001", "ART-001")


def test_license_metadata_preserves_declared_fields() -> None:
    """License metadata must preserve declared values without inference."""

    metadata = LicenseMetadata(
        license_identifier="SPDX-INTERNAL",
        rights_holder="COSMOS PVT LTD",
        confidentiality_classification="INTERNAL",
    )

    mapping = metadata.to_mapping()

    assert mapping["license_identifier"] == "SPDX-INTERNAL"
    assert mapping["rights_holder"] == "COSMOS PVT LTD"


def test_integrity_service_wraps_core_operations() -> None:
    """IntegrityService must expose deterministic digest helpers."""

    service = IntegrityService()
    content = b"service-test"

    assert service.digest_bytes(content) == sha256_bytes_digest(content)
    service.verify_bytes(content, sha256_bytes_digest(content))
