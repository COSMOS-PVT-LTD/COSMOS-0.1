"""Image hashing and non-destructive preprocessing records."""

from __future__ import annotations

from dataclasses import dataclass

from knowledge.source.integrity import sha256_bytes_digest

__all__ = ("PreprocessRecord", "hash_image", "preprocess_record")


@dataclass(frozen=True, slots=True, kw_only=True)
class PreprocessRecord:
    original_hash: str
    processed_hash: str
    operations: tuple[str, ...]


def hash_image(image: bytes) -> str:
    return sha256_bytes_digest(image)


def preprocess_record(original: bytes, *, operations: tuple[str, ...] = ()) -> PreprocessRecord:
    """Record requested operations without destroying the original bytes."""

    return PreprocessRecord(
        original_hash=hash_image(original),
        processed_hash=hash_image(original),
        operations=operations,
    )
