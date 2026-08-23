"""
COSMOS Knowledge Foundation

Module:
    knowledge.source.integrity

Purpose:
    Deterministic source and artifact integrity hashing (NEW KG-006).
"""

from __future__ import annotations

import hashlib

from knowledge.graph.source_identity import is_valid_sha256_hex
from knowledge.source.exceptions import (
    IntegrityMismatchError,
    IntegrityValidationError,
)

__all__ = (
    "IntegrityService",
    "sha256_bytes_digest",
    "sha256_text_digest",
    "verify_digest",
)


def sha256_bytes_digest(content: bytes) -> str:
    """Return a lowercase SHA-256 hex digest for byte content."""

    if not isinstance(content, bytes):
        raise IntegrityValidationError("content must be bytes.")

    return hashlib.sha256(content).hexdigest()


def sha256_text_digest(text: str) -> str:
    """Return a lowercase SHA-256 hex digest for UTF-8 text."""

    if not isinstance(text, str):
        raise IntegrityValidationError("text must be a string.")

    return sha256_bytes_digest(text.encode("utf-8"))


def verify_digest(content: bytes, expected_digest: str) -> None:
    """Raise when content does not match the expected SHA-256 digest."""

    if not is_valid_sha256_hex(expected_digest):
        raise IntegrityValidationError(
            "expected_digest must be a 64-character hexadecimal SHA-256 digest."
        )

    actual = sha256_bytes_digest(content)

    if actual != expected_digest.lower():
        raise IntegrityMismatchError(
            "Content digest does not match the expected SHA-256 value."
        )


class IntegrityService:
    """Deterministic integrity operations for source artifacts."""

    def digest_bytes(self, content: bytes) -> str:
        """Return the SHA-256 digest for byte content."""

        return sha256_bytes_digest(content)

    def digest_text(self, text: str) -> str:
        """Return the SHA-256 digest for UTF-8 text."""

        return sha256_text_digest(text)

    def verify_bytes(self, content: bytes, expected_digest: str) -> None:
        """Verify byte content against an expected digest."""

        verify_digest(content, expected_digest)

    def verify_text(self, text: str, expected_digest: str) -> None:
        """Verify UTF-8 text against an expected digest."""

        verify_digest(text.encode("utf-8"), expected_digest)
