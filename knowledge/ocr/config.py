"""Rasterization and OCR configuration records. Source PDFs are never mutated."""

from __future__ import annotations

from dataclasses import dataclass

from knowledge.source.integrity import sha256_text_digest

__all__ = ("OCRConfiguration", "RasterConfiguration", "configuration_hash")


@dataclass(frozen=True, slots=True, kw_only=True)
class RasterConfiguration:
    dpi: int = 200
    image_format: str = "png"
    color_mode: str = "rgb"
    rotation_degrees: int = 0


@dataclass(frozen=True, slots=True, kw_only=True)
class OCRConfiguration:
    language: str = "eng"
    page_segmentation_mode: int = 6
    timeout_seconds: int = 60
    low_confidence_threshold: float = 60.0


def configuration_hash(items: tuple[str, ...]) -> str:
    return sha256_text_digest("|".join(items))
