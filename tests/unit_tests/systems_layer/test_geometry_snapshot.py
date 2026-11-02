from dataclasses import FrozenInstanceError, replace

import pytest

from core.quantity import Quantity, QuantityKind
from core.unit import SI
from systems.contracts.geometry import (
    CoordinateFrame,
    DesignSnapshot,
    GeometryContractError,
    SIParameter,
    SourceReference,
)
from tests.fixtures.geometry_contracts import HASH, IDENTITY, STAMP, snapshot


@pytest.mark.parametrize("value,source,target,expected", [(10, "mm", "m", .01), (50, "bar", "Pa", 5e6), (25, "degC", "K", 298.15)])
def test_explicit_core_si_conversion(value, source, target, expected):
    original = Quantity(value, SI.get(source))
    converted = SIParameter.from_quantity("input", original, si_unit=target, source_ref_id="source")
    assert converted.value_si == expected
    assert converted.unit_symbol == target
    assert original.unit.symbol == source and original.magnitude == value


def test_temperature_interval_semantics_preserved():
    value = Quantity(10, SI.get("K"), QuantityKind.INTERVAL)
    assert SIParameter.from_quantity("delta", value, si_unit="K", source_ref_id="source").kind is QuantityKind.INTERVAL


@pytest.mark.parametrize("value", [True, False, "1", float("nan"), float("inf"), -float("inf"), 10**500])
def test_nonfinite_or_untyped_numbers_rejected(value):
    with pytest.raises(GeometryContractError):
        replace(snapshot().parameters_si[0], value_si=value)


@pytest.mark.parametrize("unit", ["mm", "bar", "degC", "unknown", "M", ""])
def test_internal_noncanonical_or_non_si_units_rejected(unit):
    with pytest.raises(GeometryContractError):
        replace(snapshot().parameters_si[0], unit_symbol=unit)


def test_dimension_and_explicit_conversion_mismatch():
    with pytest.raises(GeometryContractError, match="Dimension"):
        replace(snapshot().parameters_si[0], dimension=(0,) * 7)
    with pytest.raises(GeometryContractError):
        SIParameter.from_quantity("pressure", Quantity(50, SI.get("bar")), si_unit="m", source_ref_id="source")


def test_deep_immutability_copies_input_lists_and_returns_independent_dictionaries():
    value = snapshot()
    parameters = list(value.parameters_si)
    result = replace(value, parameters_si=parameters)
    parameters.clear()
    assert len(result.parameters_si) == 3
    with pytest.raises(FrozenInstanceError):
        result.revision_id = "overwritten"
    with pytest.raises(FrozenInstanceError):
        result.parameters_si[0].value_si = 100
    dto = result.to_canonical_dict()
    dto["parameters_si"][0]["value_si"] = 500
    assert result.parameters_si[0].value_si != 500


def test_float_roundtrip_does_not_apply_core_16_digit_rounding():
    value = replace(snapshot().parameters_si[0], value_si=1.0000000000000002)
    restored = SIParameter.from_json(value.to_json())
    assert restored.value_si.hex() == value.value_si.hex()
    assert restored.content_sha256 != replace(value, value_si=1.0).content_sha256


def test_snapshot_order_and_hash_are_deterministic():
    value = snapshot()
    reordered = replace(value, parameters_si=list(reversed(value.parameters_si)))
    assert value.to_json() == reordered.to_json()
    assert value == DesignSnapshot.from_json(value.to_json())
    assert value.content_sha256 != replace(value, revision_id="r2").content_sha256


@pytest.mark.parametrize("changes", [
    {"origin_m": (0, 0)}, {"rotation": (1,) * 9},
    {"rotation": (-1, 0, 0, 0, 1, 0, 0, 0, 1)},
    {"rotation": (1e308,) * 9}, {"units": "mm"}, {"handedness": "left"},
    {"origin_m": (float("nan"), 0, 0)}, {"parent_frame_id": "world"},
])
def test_invalid_frames_rejected(changes):
    with pytest.raises(GeometryContractError):
        replace(snapshot().frames[0], **changes)


def test_valid_translated_rotated_frame_and_ancestor_tree():
    value = snapshot()
    child = CoordinateFrame("local", "world", (.1, .2, .3), (0, -1, 0, 1, 0, 0, 0, 0, 1))
    nested = replace(value, frames=(*value.frames, child), frame_id="local")
    assert nested == DesignSnapshot.from_json(nested.to_json())


@pytest.mark.parametrize("frames", [
    (CoordinateFrame("world", None, (0, 0, 0), IDENTITY), CoordinateFrame("child", "missing", (0, 0, 0), IDENTITY)),
    (CoordinateFrame("world", None, (0, 0, 0), IDENTITY), CoordinateFrame("a", "b", (0, 0, 0), IDENTITY), CoordinateFrame("b", "a", (0, 0, 0), IDENTITY)),
    (CoordinateFrame("world", None, (0, 0, 0), IDENTITY), CoordinateFrame("other", None, (0, 0, 0), IDENTITY)),
])
def test_dangling_cycles_and_disconnected_frame_roots_rejected(frames):
    with pytest.raises(GeometryContractError):
        replace(snapshot(), frames=frames)


def test_duplicate_parameters_sources_and_unknown_reference_rejected():
    value = snapshot()
    for changes in [{"parameters_si": value.parameters_si * 2}, {"source_refs": value.source_refs * 2},
                    {"parameters_si": (replace(value.parameters_si[0], source_ref_id="missing"),)}, {"frame_id": "missing"}]:
        with pytest.raises(GeometryContractError):
            replace(value, **changes)


@pytest.mark.parametrize("uri", ["", "../secret", "/etc/passwd", "https://user:password@example.com/x", "file:///tmp/x", "javascript:alert", "https://example.com/%2e%2e/x", "a\\b", "https://[", "https://[::1", "https://example.com:invalid/x"])
def test_unsafe_provenance_uris_rejected(uri):
    with pytest.raises(GeometryContractError):
        SourceReference("source", uri, HASH)


@pytest.mark.parametrize("stamp", ["yesterday", "2026-10-09T00:00:00", "2026-10-09T00:00:00+05:30"])
def test_naive_or_non_utc_timestamps_rejected(stamp):
    with pytest.raises(GeometryContractError):
        replace(snapshot(), created_at=stamp)


def test_equivalent_utc_spelling_has_identical_digest():
    assert snapshot().content_sha256 == replace(snapshot(), created_at=STAMP.replace("+00:00", "Z")).content_sha256
