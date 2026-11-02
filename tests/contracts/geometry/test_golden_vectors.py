"""Retained byte/hash conformance vectors, not executed native-worker evidence."""
import json
from pathlib import Path

import pytest

from systems.contracts.geometry.schema import CONTRACT_TYPES

VECTORS = json.loads(Path(__file__).with_name("golden-v1.json").read_text())["vectors"]
TYPES = {cls.__name__: cls for cls in CONTRACT_TYPES}


@pytest.mark.parametrize("vector", VECTORS, ids=[v["contract_type"] + "-" + str(i) for i, v in enumerate(VECTORS)])
def test_retained_wire_bytes_and_hashes_are_unchanged(vector):
    value = TYPES[vector["contract_type"]].from_json(vector["canonical_json"])
    assert value.to_json() == vector["canonical_json"]
    assert value.content_sha256 == vector["content_sha256"]
