"""Write original COSMOS extractable PDFs — not a general publisher."""

from __future__ import annotations

__all__ = ("write_extractable_pdf", "write_image_only_pdf", "write_mixed_pdf")


def write_extractable_pdf(pages: tuple[tuple[str, ...], ...]) -> bytes:
    """Create a multi-page PDF whose text is recoverable via Tj operators."""

    if not pages:
        raise ValueError("pages must not be empty.")
    objects: list[bytes] = [
        b"1 0 obj << /Type /Catalog /Pages 2 0 R >> endobj\n",
    ]
    kids = " ".join(f"{index} 0 R" for index in range(3, 3 + len(pages)))
    objects.append(
        f"2 0 obj << /Type /Pages /Kids [{kids}] /Count {len(pages)} >> endobj\n".encode(),
    )
    font_id = 3 + (2 * len(pages))
    next_id = 3
    for page in pages:
        content_id = next_id + 1
        stream = _page_stream(page)
        objects.append(
            (
                f"{next_id} 0 obj << /Type /Page /Parent 2 0 R "
                f"/MediaBox [0 0 612 792] /Contents {content_id} 0 R "
                f"/Resources << /Font << /F1 {font_id} 0 R >> >> >> endobj\n"
            ).encode(),
        )
        objects.append(
            f"{content_id} 0 obj << /Length {len(stream)} >> stream\n".encode()
            + stream
            + b"\nendstream endobj\n",
        )
        next_id += 2
    objects.append(
        f"{font_id} 0 obj << /Type /Font /Subtype /Type1 /BaseFont /Helvetica >> endobj\n".encode(),
    )
    return _assemble(objects)


def write_mixed_pdf(text_page: tuple[str, ...]) -> bytes:
    """Page 1 has recoverable text; page 2 has no text layer."""

    return write_extractable_pdf((text_page, ()))


def write_image_only_pdf() -> bytes:
    """Create a PDF with no recoverable text layer."""

    objects = [
        b"1 0 obj << /Type /Catalog /Pages 2 0 R >> endobj\n",
        b"2 0 obj << /Type /Pages /Kids [3 0 R] /Count 1 >> endobj\n",
        b"3 0 obj << /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] >> endobj\n",
    ]
    return _assemble(objects)


def _page_stream(lines: tuple[str, ...]) -> bytes:
    commands = ["BT /F1 12 Tf 72 720 Td"]
    for index, line in enumerate(lines):
        escaped = line.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")
        if index:
            commands.append("0 -16 Td")
        commands.append(f"({escaped}) Tj")
    commands.append("ET")
    return "\n".join(commands).encode("latin-1", errors="replace")


def _assemble(objects: list[bytes]) -> bytes:
    header = b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n"
    body = b"".join(objects)
    offsets: list[int] = []
    cursor = len(header)
    for obj in objects:
        offsets.append(cursor)
        cursor += len(obj)
    xref = [f"xref\n0 {len(objects) + 1}\n0000000000 65535 f \n".encode()]
    xref.extend(f"{offset:010d} 00000 n \n".encode() for offset in offsets)
    trailer = (
        f"trailer << /Size {len(objects) + 1} /Root 1 0 R >>\nstartxref\n{cursor}\n%%EOF\n".encode()
    )
    return header + body + b"".join(xref) + trailer
