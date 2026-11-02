from email.message import Message
from io import BytesIO
from types import SimpleNamespace

import pytest

from infrastructure.transport.multipart import read_multipart_upload


def upload(data, extra=b""):
    body = b'--test\r\nContent-Disposition: form-data; name="file"; filename="data.bin"\r\nContent-Type: application/octet-stream\r\n\r\n' + data + b'\r\n' + extra + b'--test--\r\n'
    headers = Message()
    headers["Content-Length"] = str(len(body))
    headers["Content-Type"] = "multipart/form-data; boundary=test"
    return SimpleNamespace(headers=headers, rfile=BytesIO(body))


@pytest.mark.parametrize("data", [b"payload\r\n", b"binary--", bytes(range(256)), b"x\r\n\r\n"])
def test_upload_bytes_are_exact(data):
    assert read_multipart_upload(upload(data))[1] == data


def test_oversize_rejected_before_read():
    handler = upload(b"123")
    with pytest.raises(ValueError):
        read_multipart_upload(handler, max_body=2)
    assert handler.rfile.tell() == 0


def test_multiple_files_refused():
    extra = b'--test\r\nContent-Disposition: form-data; name="file"; filename="second"\r\n\r\nx\r\n'
    with pytest.raises(ValueError):
        read_multipart_upload(upload(b"one", extra))
