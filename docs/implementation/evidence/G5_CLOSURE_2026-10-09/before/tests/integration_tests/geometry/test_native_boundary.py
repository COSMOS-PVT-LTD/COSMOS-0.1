import hashlib
import json
from dataclasses import replace

import pytest

from infrastructure.geometry import WorkerCommand, WorkerSupervisor
from plugins.geometry.protocol import payload
from tests.fixtures.ngg_cases import case

from .conftest import command


@pytest.mark.parametrize("defect,expected", [("units", "INVALID_UNIT"), ("stale", "STALE_REQUEST"), ("version", "SCHEMA_VERSION"), ("hash", "HASH_MISMATCH")])
def test_actual_pico_native_input_refusal(native_config, tmp_path, defect, expected):
    s, g, r = case()
    envelope = json.loads(payload("negative", r, s, g))
    if defect == "units":
        envelope["wires"]["snapshot"] = envelope["wires"]["snapshot"].replace('"unit_symbol":"m"', '"unit_symbol":"mm"')
    elif defect == "stale":
        envelope["wires"]["request"] = replace(r, snapshot_id="a"*64).to_json()
    elif defect == "version":
        envelope["wires"]["request"] = envelope["wires"]["request"].replace('"schema_version":"1.0.0"', '"schema_version":"2.0.0"')
    else:
        envelope["wires"]["snapshot"] += " "
    if defect != "hash":
        envelope["wire_sha256"] = {name: hashlib.sha256(wire.encode()).hexdigest() for name, wire in envelope["wires"].items()}
    native = command(native_config, "picogk")
    with WorkerSupervisor() as supervisor:
        result = supervisor.submit("negative", WorkerCommand((*native.argv, str(tmp_path)), native.environment), json.dumps(envelope).encode(), tmp_path).result(timeout=10)
    assert result.code == "WORKER_CRASH" and result.exit_code == 2
    event = json.loads(result.stdout)
    assert event["event_type"] == "failed" and event["code"] == expected and not list(tmp_path.iterdir())


def test_missing_native_binary_never_falls_back(native_config, tmp_path):
    native = command(native_config, "picogk")
    broken = WorkerCommand((native.argv[0], str(tmp_path / "missing-PicoWorker.dll")), native.environment)
    with WorkerSupervisor() as supervisor:
        result = supervisor.submit("missing", broken, b"{}", tmp_path).result(timeout=10)
    assert result.code == "WORKER_CRASH" and not list(tmp_path.iterdir())
