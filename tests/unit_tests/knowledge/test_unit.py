"""
Unit tests for knowledge.models.unit.

Phase 0.5.4E — Section 1

Construction and validation tests.
"""

from __future__ import annotations

from datetime import datetime
from datetime import timezone

import pytest # type: ignore

from knowledge.models.document import Document
from knowledge.models.document import DocumentType
from knowledge.models.reference import Reference
from knowledge.models.reference import ReferenceType
from knowledge.models.unit import QuantityType
from knowledge.models.unit import Unit
from knowledge.models.unit import UnitCategory
from knowledge.models.unit import UnitStatus
from knowledge.models.unit import UnitSystem


def create_reference() -> Reference:
    """Create a valid Reference."""

    return Reference(
        reference_id="REF-001",
        reference_type=ReferenceType.NASA_REPORT,
        authors=("NASA",),
        title="Rocket Propulsion",
        publication_year=1971,
    )


def create_document() -> Document:
    """Create a valid Document."""

    return Document(
        document_id="DOC-001",
        document_version_id="1.0",
        document_type=DocumentType.TECHNICAL_NOTE,
        title="Rocket Engineering",
        content="Engineering document.",
        reference=create_reference(),
    )


def create_unit() -> Unit:
    """Create a valid Unit."""

    return Unit(
        unit_id="UNIT-001",
        name="Pascal",
        symbol="Pa",
        description="SI pressure unit.",

        category=UnitCategory.PRESSURE,
        system=UnitSystem.SI,
        quantity_type=QuantityType.SCALAR,
        status=UnitStatus.ACTIVE,

        dimension=None,
        is_si_base=False,
        is_dimensionless=False,
        is_exact=True,

        scale_factor=1.0,
        offset=0.0,

        quantity_name="Pressure",
        quantity_description="Pressure quantity.",

        aliases=("pascal",),
        common_names=("pressure unit",),
        search_keywords=("pressure", "SI"),

        source_reference=create_reference(),
        source_document=create_document(),

        version="1.0",
        status_note="Approved",

        created_timestamp=datetime.now(timezone.utc),
        modified_timestamp=datetime.now(timezone.utc),

        created_by="COSMOS",
        approved_by="Chief Engineer",
        approved_timestamp=datetime.now(timezone.utc),

        symbolic_representation="Pa",
        canonical_symbol="Pa",
    )


def test_valid_construction() -> None:
    """Verify a valid Unit can be constructed."""

    unit = create_unit()

    assert unit.unit_id == "UNIT-001"
    assert unit.name == "Pascal"
    assert unit.symbol == "Pa"


def test_blank_unit_id() -> None:
    """Blank unit identifiers shall be rejected."""

    payload = create_unit().to_dict()

    payload["unit_id"] = ""

    with pytest.raises(ValueError):
        Unit.from_dict(payload)


def test_blank_name() -> None:
    """Blank names shall be rejected."""

    payload = create_unit().to_dict()

    payload["name"] = ""

    with pytest.raises(ValueError):
        Unit.from_dict(payload)


def test_blank_symbol() -> None:
    """Blank symbols shall be rejected."""

    payload = create_unit().to_dict()

    payload["symbol"] = ""

    with pytest.raises(ValueError):
        Unit.from_dict(payload)


def test_zero_scale_factor() -> None:
    """Zero scale factors shall be rejected."""

    payload = create_unit().to_dict()

    payload["scale_factor"] = 0.0

    with pytest.raises(ValueError):
        Unit.from_dict(payload)


def test_invalid_category() -> None:
    """Invalid categories shall be rejected."""

    payload = create_unit().to_dict()

    payload["category"] = "INVALID"

    with pytest.raises(ValueError):
        Unit.from_dict(payload)


def test_invalid_system() -> None:
    """Invalid unit systems shall be rejected."""

    payload = create_unit().to_dict()

    payload["system"] = "INVALID"

    with pytest.raises(ValueError):
        Unit.from_dict(payload)

# ============================================================
# Serialization Tests
# ============================================================

def test_to_dict_returns_dictionary() -> None:
    """Verify to_dict() returns a dictionary."""

    unit = create_unit()

    data = unit.to_dict()

    assert isinstance(data, dict)


def test_to_dict_serializes_enums() -> None:
    """Verify enums are serialized using their values."""

    unit = create_unit()

    data = unit.to_dict()

    assert data["category"] == unit.category.value
    assert data["system"] == unit.system.value
    assert data["quantity_type"] == unit.quantity_type.value
    assert data["status"] == unit.status.value


def test_to_dict_serializes_reference() -> None:
    """Verify Reference objects serialize correctly."""

    unit = create_unit()

    data = unit.to_dict()

    assert isinstance(
        data["source_reference"],
        dict,
    )


def test_to_dict_serializes_document() -> None:
    """Verify Document objects serialize correctly."""

    unit = create_unit()

    data = unit.to_dict()

    assert isinstance(
        data["source_document"],
        dict,
    )


def test_to_dict_serializes_datetimes() -> None:
    """Verify datetimes become ISO-8601 strings."""

    unit = create_unit()

    data = unit.to_dict()

    assert isinstance(
        data["created_timestamp"],
        str,
    )

    assert isinstance(
        data["modified_timestamp"],
        str,
    )

    assert isinstance(
        data["approved_timestamp"],
        str,
    )


def test_to_dict_serializes_tuples() -> None:
    """Verify tuples become lists."""

    unit = create_unit()

    data = unit.to_dict()

    assert isinstance(
        data["aliases"],
        list,
    )

    assert isinstance(
        data["common_names"],
        list,
    )

    assert isinstance(
        data["search_keywords"],
        list,
    )


def test_from_dict_reconstructs_unit() -> None:
    """Verify Unit reconstruction."""

    original = create_unit()

    reconstructed = Unit.from_dict(
        original.to_dict()
    )

    assert isinstance(
        reconstructed,
        Unit,
    )


def test_round_trip_serialization() -> None:
    """Verify deterministic serialization."""

    original = create_unit()

    reconstructed = Unit.from_dict(
        original.to_dict()
    )

    assert (
        reconstructed.to_dict()
        == original.to_dict()
    )


def test_round_trip_identity() -> None:
    """Verify important fields survive reconstruction."""

    original = create_unit()

    reconstructed = Unit.from_dict(
        original.to_dict()
    )

    assert (
        reconstructed.unit_id
        == original.unit_id
    )

    assert (
        reconstructed.name
        == original.name
    )

    assert (
        reconstructed.symbol
        == original.symbol
    )

    assert (
        reconstructed.scale_factor
        == original.scale_factor
    )

    assert (
        reconstructed.offset
        == original.offset
    )


def test_invalid_from_dict_type() -> None:
    """from_dict shall reject non-dictionaries."""

    with pytest.raises(TypeError):
        Unit.from_dict(
            "invalid"  # type: ignore[arg-type]
        )


def test_missing_required_field() -> None:
    """Missing required fields shall be rejected."""

    payload = create_unit().to_dict()

    del payload["unit_id"]

    with pytest.raises(
        (
            KeyError,
            ValueError,
        )
    ):
        Unit.from_dict(payload)

# ============================================================
# Query Methods & Object Semantics
# ============================================================


def test_display_name() -> None:
    """Verify display_name()."""

    unit = create_unit()

    assert unit.display_name() == "Pascal (Pa)"


def test_matches_alias() -> None:
    """Verify alias matching."""

    unit = create_unit()

    assert unit.matches_alias("pascal")
    assert unit.matches_alias("PASCAL")
    assert not unit.matches_alias("meter")


def test_matches_keyword() -> None:
    """Verify keyword matching."""

    unit = create_unit()

    assert unit.matches_keyword("pressure")
    assert unit.matches_keyword("SI")
    assert not unit.matches_keyword("rocket")


def test_has_reference() -> None:
    """Verify reference detection."""

    unit = create_unit()

    assert unit.has_reference()


def test_has_document() -> None:
    """Verify document detection."""

    unit = create_unit()

    assert unit.has_document()


def test_alias_count() -> None:
    """Verify alias counting."""

    unit = create_unit()

    assert len(unit.aliases) == 1


def test_common_name_count() -> None:
    """Verify common-name counting."""

    unit = create_unit()

    assert len(unit.common_names) == 1


def test_keyword_count() -> None:
    """Verify keyword counting."""

    unit = create_unit()

    assert len(unit.search_keywords) == 2


# ============================================================
# Object Semantics
# ============================================================


def test_immutable() -> None:
    """Verify Unit is immutable."""

    from dataclasses import FrozenInstanceError

    unit = create_unit()

    with pytest.raises(
        (
            FrozenInstanceError,
            AttributeError,
        )
    ):
        unit.name = "Modified"  # type: ignore[misc]


def test_unit_equality() -> None:
    """Verify equality semantics."""

    unit1 = create_unit()

    unit2 = Unit.from_dict(
        unit1.to_dict()
    )

    assert unit1 == unit2


def test_unit_inequality() -> None:
    """Verify inequality semantics."""

    payload = create_unit().to_dict()

    payload["unit_id"] = "UNIT-999"

    unit2 = Unit.from_dict(payload)

    assert create_unit() != unit2

@pytest.mark.skip(
    reason=(
        "Document contains mappingproxy and is "
        "not yet hashable."
    ),
)
def test_unit_hashable() -> None:
    """Verify Unit is hashable."""

    unit = create_unit()

    unit_set = {unit}

    assert unit in unit_set


def test_copy() -> None:
    """Verify immutable copy()."""

    unit = create_unit()

    copied = unit.copy()

    assert copied == unit
    assert copied is not unit


def test_serialize_alias() -> None:
    """Verify serialize()."""

    unit = create_unit()

    assert (
        unit.serialize()
        == unit.to_dict()
    )


def test_deserialize_alias() -> None:
    """Verify deserialize()."""

    unit = create_unit()

    reconstructed = Unit.deserialize(
        unit.serialize()
    )

    assert reconstructed == unit


def test_iter() -> None:
    """Verify __iter__()."""

    unit = create_unit()

    items = list(unit)

    assert len(items) == len(unit)


def test_len() -> None:
    """Verify __len__()."""

    unit = create_unit()

    assert len(unit) == len(
        unit.to_dict()
    )


def test_deterministic_serialization() -> None:
    """Serialization shall be deterministic."""

    unit = create_unit()

    assert (
        unit.to_dict()
        == unit.to_dict()
    )


