"""Independent shape validation; runtime invariants use the typed decoder too."""
import json
from pathlib import Path

import pytest

from systems.contracts.geometry.schema import CONTRACT_TYPES, schema_document
from tests.fixtures.geometry_contracts import all_contracts, record

jsonschema = pytest.importorskip("jsonschema", reason="Install pinned optional geometry contract test tooling")


def validator():
    schema = schema_document()
    jsonschema.Draft202012Validator.check_schema(schema)
    return jsonschema.Draft202012Validator(schema, format_checker=jsonschema.FormatChecker())


def test_static_schema_exactly_matches_authoritative_dataclass_schema():
    root = Path(__file__).resolve().parents[3]
    static = json.loads((root / "systems/contracts/geometry/schemas/geometry-v1.schema.json").read_text())
    assert static == schema_document()
    assert len(static["$defs"]) == len(CONTRACT_TYPES) == 13


@pytest.mark.parametrize("index", range(13))
def test_schema_and_typed_request_response_serialization(index):
    instance = all_contracts()[index]
    dto = instance.to_canonical_dict()
    validator().validate(dto)
    assert type(instance).from_json(json.dumps(dto)) == instance


@pytest.mark.parametrize("mutation", ["unknown_field", "version", "boolean_seq", "negative_progress", "unsafe_path", "wrong_units", "missing_hash"])
def test_independent_schema_rejects_invalid_worker_shapes(mutation):
    dto = record().to_canonical_dict()
    if mutation == "unknown_field":
        dto["successful_and_validated"] = True
    elif mutation == "version":
        dto["schema_version"] = "later"
    elif mutation == "boolean_seq":
        dto["events"][0]["seq"] = True
    elif mutation == "negative_progress":
        dto["events"][0]["progress_fraction"] = -1
    elif mutation == "unsafe_path":
        dto["artifacts"][0]["storage_uri"] = "../private.step"
    elif mutation == "wrong_units":
        dto["artifacts"][0]["units"] = "mm"
    else:
        dto["artifacts"][0].pop("sha256")
    with pytest.raises(jsonschema.ValidationError):
        validator().validate(dto)
