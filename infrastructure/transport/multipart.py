"""Bounded browser-form transport; uploaded bytes are never stripped or rewritten."""
from __future__ import annotations

from email import policy
from email.message import Message
from email.parser import BytesParser
from http.server import BaseHTTPRequestHandler

LEGACY_BODY_LIMIT = 101 * 1024**2
PREVIEW_FILE_LIMIT = 15 * 1024**2


def multipart_boundary(content_type: str) -> str:
    if not content_type.isascii() or "\r" in content_type or "\n" in content_type:
        raise ValueError("Invalid multipart content type")
    header = Message()
    header["Content-Type"] = content_type
    parameters = header.get_params() or []
    if header.get_content_type() != "multipart/form-data":
        raise ValueError("Upload requires multipart/form-data")
    boundaries = [value for key, value in parameters[1:] if key.lower() == "boundary"]
    if len(boundaries) != 1:
        raise ValueError("One multipart boundary is required")
    boundary = boundaries[0]
    if not isinstance(boundary, str) or not 1 <= len(boundary) <= 70:
        raise ValueError("Multipart boundary must contain 1 to 70 ASCII characters")
    if not boundary.isascii() or any(ord(char) < 33 or ord(char) > 126 for char in boundary):
        raise ValueError("Multipart boundary contains unsupported characters")
    return boundary


def read_multipart_upload(
    handler: BaseHTTPRequestHandler, *, max_body: int = LEGACY_BODY_LIMIT,
    max_file: int = 100 * 1024**2,
) -> tuple[str, bytes, dict[str, str]]:
    lengths = handler.headers.get_all("Content-Length", [])
    types = handler.headers.get_all("Content-Type", [])
    if handler.headers.get_all("Transfer-Encoding", []) or len(lengths) != 1 or len(types) != 1:
        raise ValueError("One unambiguous upload length and content type are required")
    value = lengths[0]
    if len(value) > 9 or not value.isascii() or not value.isdecimal():
        raise ValueError("Invalid upload length")
    length = int(value)
    if not 0 < length <= max_body:
        raise ValueError("Upload exceeds the request size limit")
    boundary = multipart_boundary(types[0])
    body = handler.rfile.read(length)
    if len(body) != length or not body.endswith((b"--" + boundary.encode() + b"--\r\n", b"--" + boundary.encode() + b"--")):
        raise ValueError("Incomplete multipart upload")
    message = BytesParser(policy=policy.default).parsebytes(
        b"Content-Type: " + types[0].encode("ascii") + b"\r\nMIME-Version: 1.0\r\n\r\n" + body,
    )
    if message.defects or not message.is_multipart():
        raise ValueError("Malformed multipart upload")
    fields: dict[str, str] = {}
    file_value: tuple[str, bytes] | None = None
    parts = list(message.iter_parts())
    if not 1 <= len(parts) <= 16:
        raise ValueError("Upload has too many fields")
    names: set[str] = set()
    for part in parts:
        if part.defects or part.is_multipart() or part.get_content_disposition() != "form-data":
            raise ValueError("Malformed or nested multipart field")
        if sum(len(key) + len(value) for key, value in part.raw_items()) > 8192 or len(part.get_all("Content-Disposition", [])) != 1:
            raise ValueError("Upload field headers exceed the allowed limit")
        if part.get("Content-Transfer-Encoding") not in {None, "binary", "8bit"}:
            raise ValueError("Encoded multipart fields are unsupported")
        name = part.get_param("name", header="content-disposition")
        if not isinstance(name, str) or not name or name in names:
            raise ValueError("Duplicate or unnamed multipart field")
        names.add(name)
        data = part.get_payload(decode=True)
        if not isinstance(data, bytes):
            raise ValueError("Invalid multipart payload")  # noqa: TRY004 -- malformed wire data, not a Python caller type
        filename = part.get_filename()
        if filename is not None:
            if name != "file" or file_value is not None or not filename or not 0 < len(data) <= max_file:
                raise ValueError("One nonempty file within the upload size limit is required")
            file_value = (filename, data)
        else:
            if len(data) > 64 * 1024:
                raise ValueError("Upload text field exceeds the limit")
            fields[name] = data.decode("utf-8")
    if file_value is None:
        raise ValueError("File field missing")
    return file_value[0], file_value[1], fields
