"""Embedded-image inventory. Missing bytes are not fabricated."""

from __future__ import annotations

from dataclasses import dataclass
import re

__all__ = ("EmbeddedImageRef", "list_embedded_images")

_IMAGE = re.compile(rb"/Subtype\s*/Image")


@dataclass(frozen=True, slots=True, kw_only=True)
class EmbeddedImageRef:
    image_id: str
    page_number: int | None
    bytes_available: bool
    warning: str


def list_embedded_images(content: bytes) -> tuple[EmbeddedImageRef, ...]:
    count = len(_IMAGE.findall(content))
    if count == 0:
        return ()
    return tuple(
        EmbeddedImageRef(
            image_id=f"img-{index}",
            page_number=None,
            bytes_available=False,
            warning="Embedded image object present but pixel bytes are not extracted.",
        )
        for index in range(1, count + 1)
    )
