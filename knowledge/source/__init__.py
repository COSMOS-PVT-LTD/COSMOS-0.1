"""Public exports for knowledge.source (KG-BLOCK-005 W1)."""

from __future__ import annotations

from knowledge.source.exceptions import (
    IntegrityError,
    IntegrityMismatchError,
    IntegrityValidationError,
    LicenseMetadataError,
    SourceSystemError,
    VaultError,
    VaultNotFoundError,
    VaultValidationError,
)
from knowledge.source.integrity import (
    IntegrityService,
    sha256_bytes_digest,
    sha256_text_digest,
    verify_digest,
)
from knowledge.source.license import LicenseMetadata
from knowledge.source.vault import (
    InMemorySourceVault,
    SourceVault,
    VaultArtifact,
    VaultArtifactMetadata,
)

__all__ = (
    "InMemorySourceVault",
    "IntegrityError",
    "IntegrityMismatchError",
    "IntegrityService",
    "IntegrityValidationError",
    "LicenseMetadata",
    "LicenseMetadataError",
    "SourceSystemError",
    "SourceVault",
    "VaultArtifact",
    "VaultArtifactMetadata",
    "VaultError",
    "VaultNotFoundError",
    "VaultValidationError",
    "sha256_bytes_digest",
    "sha256_text_digest",
    "verify_digest",
)
