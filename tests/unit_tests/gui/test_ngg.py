import io
import json
from email.message import Message
from types import SimpleNamespace

import pytest

from gui.ngg import enabled, read_payload, transport_guard
from systems.contracts.geometry import GeometryContractError
from systems.geometry.workbench import GeometryWorkbench


@pytest.mark.parametrize("flag", [None, "", "false", "0", "invalid", "TRUE-ish"])
def test_ngg_strict_defaults_off(flag):
    assert not enabled(flag, True)


def test_ngg_requires_modern_server_flag():
    assert enabled("true", True) and not enabled("true", False)


@pytest.mark.parametrize("settings", [{}, {"operation": "sphere", "backend": "occt", "voxel_m": True},
    {"operation": "engine", "backend": "occt", "voxel_m": .0005}, {"operation": "sphere", "backend": "shell", "voxel_m": .0005},
    {"operation": "sphere", "backend": "occt", "voxel_m": .0005, "radius_m": 10}])
def test_no_arbitrary_engineering_inputs_or_worker_commands(settings):
    with pytest.raises(GeometryContractError):
        GeometryWorkbench.revision(settings)


def test_real_immutable_si_revision_and_graph_linkage():
    settings = {"operation": "difference", "backend": "picogk", "voxel_m": .0005}
    a, b = GeometryWorkbench.revision(settings), GeometryWorkbench.revision(settings)
    assert a.snapshot.snapshot_id != b.snapshot.snapshot_id
    assert a.snapshot.project_id == "p07-software-fixtures"
    assert a.graph.snapshot_id == a.request.snapshot_id == a.snapshot.snapshot_id
    assert a.request.feature_graph_sha256 == a.graph.content_sha256
    assert {p.unit_symbol for p in a.snapshot.parameters_si} == {"m"}


def handler(headers=None, body=b'{}'):
    values = {"Host": "127.0.0.1:8812", "Origin": "http://127.0.0.1:8812", "Content-Type": "application/json", "Content-Length": str(len(body)), **(headers or {})}
    request_headers = Message()
    for key, value in values.items():
        request_headers[key] = value
    return SimpleNamespace(server=SimpleNamespace(server_address=("127.0.0.1", 8812)), client_address=("127.0.0.1", 1234),
        headers=request_headers, rfile=io.BytesIO(body))


@pytest.mark.parametrize("headers", [{"Host": "attacker.example:8812"}, {"Origin": "http://evil.example"}, {"Origin": None}, {"Content-Type": "text/plain"}, {"Transfer-Encoding": "chunked"}])
def test_native_origin_host_and_content_guards(headers):
    with pytest.raises(GeometryContractError):
        transport_guard(handler(headers), mutation=True)


@pytest.mark.parametrize("body", [b'{"a":1,"a":2}', b'{"x":NaN}', b'{"x":1e999}', b'[]', b'invalid', b'\xff\xfe{\x00}\x00'])
def test_bounded_json_rejects_ambiguous_nonfinite_and_invalid_payloads(body):
    with pytest.raises((GeometryContractError, ValueError)):
        read_payload(handler(body=body))


@pytest.mark.parametrize("length", ["", "-1", "0", "16777217", "1e4"])
def test_request_length_guard_before_read(length):
    with pytest.raises(GeometryContractError):
        read_payload(handler({"Content-Length": length}))


def test_valid_payload_and_transport():
    transport_guard(handler(), mutation=True)
    assert read_payload(handler(body=json.dumps({"snapshot_id": "a"}).encode())) == {"snapshot_id": "a"}


def test_duplicate_request_length_is_refused_before_read():
    request = handler()
    request.headers["Content-Length"] = "2"
    with pytest.raises(GeometryContractError):
        read_payload(request)
    assert request.rfile.tell() == 0
