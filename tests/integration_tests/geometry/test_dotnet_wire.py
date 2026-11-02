import json
import struct
from pathlib import Path

import pytest

from infrastructure.geometry import WorkerSupervisor

from .conftest import command

ROOT = Path(__file__).resolve().parents[3]
VECTORS = json.loads((ROOT / "tests/contracts/geometry/golden-v1.json").read_text())["vectors"]


def bits(value):
    if type(value) is dict:
        return [item for key in sorted(value) for item in bits(value[key])]
    if type(value) is list:
        return [item for child in value for item in bits(child)]
    if type(value) in (float, int):
        return [struct.pack(">d", float(value)).hex()]
    return []


@pytest.mark.parametrize("vector", VECTORS, ids=[v["contract_type"] + "-" + str(i) for i, v in enumerate(VECTORS)])
def test_actual_dotnet_retained_golden_wire_and_numeric_bits(native_config, tmp_path, vector):
    with WorkerSupervisor() as supervisor:
        result = supervisor.submit("wire", command(native_config, "wire_probe"), json.dumps(vector).encode(), tmp_path).result(timeout=10)
        assert result.code == "OK", result.stderr
        response = json.loads(result.stdout)
        assert response["canonical_json"] == vector["canonical_json"] and response["content_sha256"] == vector["content_sha256"]
        assert response["number_bits"] == bits(json.loads(vector["canonical_json"]))
        assert response["semantic_validation_owner"] == "Python P06"


@pytest.mark.parametrize("defect", ["checksum", "version", "duplicate", "nonfinite"])
def test_actual_dotnet_wire_negative_conformance(native_config, tmp_path, defect):
    vector = dict(VECTORS[0])
    if defect == "checksum":
        vector["content_sha256"] = "0"*64
    elif defect == "version":
        vector["canonical_json"] = vector["canonical_json"].replace('"schema_version":"1.0.0"', '"schema_version":"2.0.0"')
    elif defect == "duplicate":
        vector["canonical_json"] = '{"ref_id":"other",' + vector["canonical_json"][1:]
    else:
        vector["canonical_json"] = '{"value":1e999,' + vector["canonical_json"][1:]
    with WorkerSupervisor() as supervisor:
        result = supervisor.submit("wire-negative", command(native_config, "wire_probe"), json.dumps(vector).encode(), tmp_path).result(timeout=10)
        assert result.code == "WORKER_CRASH" and not result.stdout
