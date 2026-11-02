import json
from dataclasses import replace

import pytest

from systems.contracts.geometry import GeometryContractError
from systems.contracts.geometry._wire import MAX_WIRE_BYTES
from tests.fixtures.geometry_contracts import all_contracts, record, snapshot


@pytest.mark.parametrize("index", range(13))
def test_all_p06_typed_contracts_independent_serialization(index):
    value = all_contracts()[index]
    assert type(value).from_canonical_dict(value.to_canonical_dict()) == value
    assert type(value).from_json(value.to_json()).to_json() == value.to_json()


@pytest.mark.parametrize("mutation", ["version", "type", "unknown", "missing", "checksum", "nested_checksum", "snapshot_identity"])
def test_untrusted_worker_or_api_payloads_reject_unknown_or_tampered_contracts(mutation):
    value = record()
    payload = value.to_canonical_dict()
    if mutation == "version":
        payload["schema_version"] = "2.0.0"
    elif mutation == "type":
        payload["contract_type"] = "Other"
    elif mutation == "unknown":
        payload["stale"] = False
    elif mutation == "missing":
        payload.pop("snapshot")
    elif mutation == "checksum":
        payload["content_sha256"] = "0" * 64
    elif mutation == "nested_checksum":
        payload["snapshot"]["parameters_si"][0]["value_si"] = .999
    else:
        payload["request"]["snapshot_id"] = "c" * 64
    with pytest.raises(GeometryContractError):
        type(value).from_canonical_dict(payload)


@pytest.mark.parametrize("raw", ["{broken", "[]", "null", '{"same":1,"same":2}', '{"float":NaN}', '{"float":Infinity}'])
def test_invalid_json_is_a_structured_error(raw):
    with pytest.raises(GeometryContractError) as failure:
        type(snapshot()).from_json(raw)
    assert failure.value.diagnostic("fixture-correlation")["recovery"]


def test_wire_payload_size_and_deep_json_rejected_without_execution():
    for raw in ['"' + "x" * MAX_WIRE_BYTES + '"', "[" * 1100 + "0" + "]" * 1100]:
        with pytest.raises(GeometryContractError):
            type(snapshot()).from_json(raw)


def test_nonfinite_canonical_dict_not_silently_encoded_as_null():
    dto = snapshot().to_canonical_dict()
    dto["parameters_si"][0]["value_si"] = float("nan")
    with pytest.raises(GeometryContractError):
        type(snapshot()).from_canonical_dict(dto)


def test_checksum_lineage_preserves_all_precision():
    first = snapshot()
    changed = replace(first, parameters_si=tuple(replace(p, value_si=1.0000000000000002) if p.name == "radius" else p for p in first.parameters_si))
    assert changed.snapshot_id != first.snapshot_id
    assert json.loads(changed.to_json())["content_sha256"] == changed.snapshot_id
