import hashlib
import json
import sys
from dataclasses import replace

import pytest

from infrastructure.geometry import ProcessResult, WorkerCommand, WorkerSupervisor
from plugins.geometry.adapters import OCCTAdapter, PicoGKAdapter
from plugins.geometry.protocol import (
    checked_file,
    parse_request,
    payload,
    validate_slice,
)
from systems.contracts.geometry import GeometryContractError, OutputFormat
from tests.fixtures.ngg_cases import case


def test_exact_p06_request_response_wire_preserves_full_precision():
    s, g, r = case()
    original = payload("job", r, s, g)
    job, action, request, snapshot, graph = parse_request(original)
    assert (job, action, request, snapshot, graph) == ("job", "build", r, s, g)
    envelope = json.loads(original)
    assert all(hashlib.sha256(text.encode()).hexdigest() == envelope["wire_sha256"][name] for name, text in envelope["wires"].items())


@pytest.mark.parametrize("mutation", ["protocol", "unknown", "job", "wire", "nested_version", "correlation", "fields", "nan"])
def test_untrusted_protocol_shapes_refused(mutation):
    s, g, r = case()
    value = json.loads(payload("job", r, s, g))
    if mutation == "protocol":
        value["protocol"] = "future"
    elif mutation == "unknown":
        value["execute_shell"] = "bad"
    elif mutation == "job":
        value["job_id"] = "../bad"
    elif mutation == "wire":
        value["wires"]["snapshot"] += " "
    elif mutation == "nested_version":
        value["wires"]["request"] = value["wires"]["request"].replace('"schema_version":"1.0.0"', '"schema_version":"2.0.0"')
        value["wire_sha256"]["request"] = hashlib.sha256(value["wires"]["request"].encode()).hexdigest()
    elif mutation == "correlation":
        value["correlation_id"] = "other"
    elif mutation == "fields":
        value["wires"] = []
    else:
        value["wires"]["request"] = "NaN"
        value["wire_sha256"]["request"] = hashlib.sha256(b"NaN").hexdigest()
    with pytest.raises(GeometryContractError):
        parse_request(json.dumps(value).encode())


def test_duplicate_key_stale_graph_and_boolean_role_guards():
    s, g, r = case()
    with pytest.raises(GeometryContractError):
        parse_request(b'{"job_id":"one","job_id":"two"}')
    with pytest.raises(GeometryContractError):
        payload("stale", r, replace(s, revision_id="r2"), g)
    s, g, r = case("difference")
    bad = replace(g.features[-1], dependency_ids=(g.features[0].feature_id, g.features[1].feature_id), operation="boolean.difference")
    assert set(bad.dependency_ids) == {"pair.lhs", "pair.rhs"}
    validate_slice(r, s, g, "picogk")


def test_backend_default_disabled_and_capabilities_are_honest(tmp_path):
    with WorkerSupervisor() as supervisor:
        command = WorkerCommand((sys.executable, "-c", "pass"))
        s, g, r = case()
        backend = PicoGKAdapter(command, supervisor)
        assert backend.capabilities().formats == ("stl",)
        assert not backend.capabilities().production_enabled
        with pytest.raises(GeometryContractError) as error:
            backend.build("disabled", r, s, g, tmp_path)
        assert error.value.code == "NGG_DISABLED"
        assert OCCTAdapter(command, supervisor).capabilities().formats == ("step", "stl")
        with pytest.raises(GeometryContractError):
            backend.export("existing", "step", 1e-6)


@pytest.mark.parametrize("changes", [{"backend_version": "unknown"}, {"backend_id": "other"}, {"voxel_resolution_m": .0001}])
def test_version_and_unqualified_resolution_refused(changes):
    s, g, r = case()
    with pytest.raises(GeometryContractError):
        validate_slice(replace(r, **changes), s, g, "picogk")


@pytest.mark.parametrize("name,sha", [("../secret.stl", "a"*64), ("export.stl", None), ("export.stl", "bad"), ("export.stl", "a"*64)])
def test_artifact_path_type_hash_guards(tmp_path, name, sha):
    (tmp_path / "export.stl").write_bytes(b"fixture bytes")
    with pytest.raises(GeometryContractError):
        checked_file(tmp_path, name, sha)


def test_symlink_rejected_even_with_matching_hash(tmp_path):
    outside = tmp_path / "outside"
    outside.write_bytes(b"fixture")
    (tmp_path / "export.stl").symlink_to(outside)
    with pytest.raises(GeometryContractError):
        checked_file(tmp_path, "export.stl", hashlib.sha256(b"fixture").hexdigest())


@pytest.mark.parametrize("raw", [b"not json", b'{"bad":NaN}', b'{"bad":1e999}', b'{"x":1,"x":2}', b'[]', b'{}'])
def test_bad_worker_response_never_accepts_files(raw, tmp_path):
    _, _, request = case()
    with WorkerSupervisor() as supervisor:
        backend = PicoGKAdapter(WorkerCommand((sys.executable, "-c", "pass")), supervisor)
        with pytest.raises(GeometryContractError):
            backend.decode(ProcessResult("job", "OK", 0, raw, b"", .1, 0, 123), request, tmp_path)


def test_unsupported_geometry_and_format_fail_explicitly(tmp_path):
    s, g, r = case()
    with WorkerSupervisor() as supervisor:
        backend = PicoGKAdapter(WorkerCommand((sys.executable, "-c", "pass")), supervisor, enabled=True)
        with pytest.raises(GeometryContractError):
            backend.build("vdb", replace(r, output_formats=(OutputFormat.VDB,)), s, g, tmp_path)
        unsupported = replace(g, features=(replace(g.features[0], operation="arbitrary.user.code"),))
        changed = replace(r, feature_graph_sha256=unsupported.content_sha256)
        with pytest.raises(GeometryContractError):
            backend.build("unsupported", changed, s, unsupported, tmp_path)
