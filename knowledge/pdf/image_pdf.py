"""COSMOS-authored scanned PDFs: render text to an image XObject, no text layer."""

from __future__ import annotations

import io
from pathlib import Path

from knowledge.pdf.writer import _assemble

__all__ = ("render_text_page_image", "write_image_pdf", "write_scanned_pdf")

_FONT_CANDIDATES = (
    "/System/Library/Fonts/Supplemental/Arial.ttf",
    "/Library/Fonts/Arial.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
)


def render_text_page_image(
    lines: tuple[str, ...],
    *,
    width: int = 1700,
    height: int = 2200,
) -> bytes:
    """Render COSMOS-original page text to PNG. Does not invent missing lines."""

    from PIL import Image, ImageDraw  # type: ignore[import-untyped]

    image = Image.new("RGB", (width, height), "white")
    draw = ImageDraw.Draw(image)
    font = _font(36)
    y = 80
    for line in lines:
        draw.text((80, y), line, fill="black", font=font)
        y += 56
        if y > height - 80:
            break
    buffer = io.BytesIO()
    image.save(buffer, format="PNG")
    return buffer.getvalue()


def write_image_pdf(image: bytes, *, page_width: int = 612, page_height: int = 792) -> bytes:
    """Embed a JPEG/PNG page image in a PDF with no recoverable text operators."""

    jpeg, width, height = _as_jpeg(image)
    stream = (
        f"q {page_width} 0 0 {page_height} 0 0 cm /Im1 Do Q\n"
    ).encode("ascii")
    objects = [
        b"1 0 obj << /Type /Catalog /Pages 2 0 R >> endobj\n",
        b"2 0 obj << /Type /Pages /Kids [3 0 R] /Count 1 >> endobj\n",
        (
            "3 0 obj << /Type /Page /Parent 2 0 R "
            f"/MediaBox [0 0 {page_width} {page_height}] "
            "/Contents 4 0 R /Resources << /XObject << /Im1 5 0 R >> >> >> endobj\n"
        ).encode(),
        f"4 0 obj << /Length {len(stream)} >> stream\n".encode() + stream + b"\nendstream endobj\n",
        (
            f"5 0 obj << /Type /XObject /Subtype /Image /Width {width} /Height {height} "
            f"/ColorSpace /DeviceRGB /BitsPerComponent 8 /Filter /DCTDecode "
            f"/Length {len(jpeg)} >> stream\n"
        ).encode()
        + jpeg
        + b"\nendstream endobj\n",
    ]
    return _assemble(objects)


def write_scanned_pdf(lines: tuple[str, ...]) -> bytes:
    return write_image_pdf(render_text_page_image(lines))


def _font(size: int):  # type: ignore[no-untyped-def]
    from PIL import ImageFont  # type: ignore[import-untyped]

    for candidate in _FONT_CANDIDATES:
        if Path(candidate).is_file():
            return ImageFont.truetype(candidate, size)
    return ImageFont.load_default()


def _as_jpeg(image: bytes) -> tuple[bytes, int, int]:
    from PIL import Image  # type: ignore[import-untyped]

    opened = Image.open(io.BytesIO(image)).convert("RGB")
    buffer = io.BytesIO()
    opened.save(buffer, format="JPEG", quality=95)
    return buffer.getvalue(), opened.size[0], opened.size[1]
