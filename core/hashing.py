"""
COSMOS Core — deterministic object identity hashing.

Maps canonical representations to stable SHA-256 digests.
"""

from __future__ import annotations

import hashlib
from collections.abc import Mapping

from core.serialization import canonical_json_dumps, to_canonical_json

__all__ = (
    "canonical_hash",
    "canonical_sha256_hex",
)


def canonical_sha256_hex(payload: str) -> str:
    """Return the SHA-256 hex digest of ``payload``."""

    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def canonical_hash(value: object) -> str:
    """
    Compute a deterministic SHA-256 digest for a canonical object.

    Parameters
    ----------
    value:
        Mapping or object exposing ``to_canonical_dict()``.

    Returns
    -------
    str
        Lowercase hexadecimal SHA-256 digest.
    """

    if isinstance(value, Mapping):
        canonical_json = canonical_json_dumps(value)
    else:
        canonical_json = to_canonical_json(value)

    return canonical_sha256_hex(canonical_json)
