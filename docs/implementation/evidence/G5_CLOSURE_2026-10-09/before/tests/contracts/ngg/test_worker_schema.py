import json
from pathlib import Path

import pytest

from plugins.geometry.protocol import payload
from tests.fixtures.ngg_cases import case


def test_envelope_schema_is_versioned_strict_and_matches_actual_payload():
    jsonschema = pytest.importorskip("jsonschema")
    schema = json.loads(Path(__file__).with_name("worker-v1.schema.json").read_text())
    jsonschema.Draft202012Validator.check_schema(schema)
    s, g, r = case()
    envelope = json.loads(payload("schema", r, s, g))
    validator = jsonschema.Draft202012Validator(schema)
    assert not list(validator.iter_errors(envelope))
    envelope["shell"] = "forbidden"
    assert list(validator.iter_errors(envelope))
