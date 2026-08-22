"""
Unit tests for knowledge.models.dimension.

Phase 0.5.5E — Section 1

Construction and validation tests.
"""

from __future__ import annotations

from datetime import datetime
from datetime import timezone

import pytest  # type: ignore

from knowledge.models.dimension import Dimension
from knowledge.models.dimension import DimensionCategory
from knowledge.models.dimension import DimensionStatus
from knowledge.models.dimension import PhysicalQuantity
from knowledge.models.document import Document
from knowledge.models.document import DocumentType
from knowledge.models.reference import Reference
from knowledge.models.reference import ReferenceType
from knowledge.models.variable import EngineeringDomain

FIXED_TIME = datetime(
    2025,
    1,
    1,
    tzinfo=timezone.utc,
)

def create_reference() -> Reference:
    """Create a valid Reference."""

    return Reference(
        reference_id="REF-001",
        reference_type=ReferenceType.BOOK,
        title="NASA SP-125",
        authors=("NASA",),
        publication_year=1971,
    )


def create_document() -> Document:
    """Create a valid Document."""

    return Document(
        document_id="DOC-001",
        document_version_id="1.0",
        document_type=DocumentType.TEXTBOOK,
        title="Rocket Engineering",
        content="Engineering document.",
        reference=create_reference(),
    )


def create_dimension() -> Dimension:
    """Create a valid Dimension."""

    return Dimension(

        # ----------------------------------------------------
        # Identity
        # ----------------------------------------------------

        dimension_id="DIM-001",
        name="Pressure",
        symbol="[M L^-1 T^-2]",
        description="Pressure dimension.",

        # ----------------------------------------------------
        # Classification
        # ----------------------------------------------------

        category=DimensionCategory.DERIVED,
        physical_quantity=PhysicalQuantity.PRESSURE,
        status=DimensionStatus.ACTIVE,

        # ----------------------------------------------------
        # SI Exponents
        # ----------------------------------------------------

        length_exponent=-1,
        mass_exponent=1,
        time_exponent=-2,
        electric_current_exponent=0,
        temperature_exponent=0,
        amount_of_substance_exponent=0,
        luminous_intensity_exponent=0,

        canonical_expression="kg·m⁻¹·s⁻²",

        is_dimensionless=False,
        is_base_dimension=False,
        is_derived_dimension=True,

        # ----------------------------------------------------
        # Engineering
        # ----------------------------------------------------

        engineering_domain=EngineeringDomain.GENERAL,
        engineering_disciplines=("Propulsion",),

        applicable_regimes=("Compressible",),

        aliases=("pressure",),

        common_names=("Pressure",),

        search_keywords=("pressure", "stress"),

        source_reference=create_reference(),

        source_document=create_document(),

        # ----------------------------------------------------
        # Repository
        # ----------------------------------------------------

        version="1.0",

        created_timestamp=FIXED_TIME,

        modified_timestamp=FIXED_TIME,

        approved_timestamp=FIXED_TIME,
    )


def test_valid_construction() -> None:
    """Verify valid construction."""

    dimension = create_dimension()

    assert dimension.dimension_id == "DIM-001"
    assert dimension.name == "Pressure"
    assert dimension.mass_exponent == 1


def test_blank_dimension_id() -> None:
    """Blank identifiers shall fail."""

    payload = create_dimension().to_dict()

    payload["dimension_id"] = ""

    with pytest.raises(ValueError):
        Dimension.from_dict(payload)


def test_blank_name() -> None:
    """Blank names shall fail."""

    payload = create_dimension().to_dict()

    payload["name"] = ""

    with pytest.raises(ValueError):
        Dimension.from_dict(payload)


def test_blank_symbol() -> None:
    """Blank symbols shall fail."""

    payload = create_dimension().to_dict()

    payload["symbol"] = ""

    with pytest.raises(ValueError):
        Dimension.from_dict(payload)


def test_invalid_category() -> None:
    """Invalid categories shall fail."""

    payload = create_dimension().to_dict()

    payload["category"] = "INVALID"

    with pytest.raises(ValueError):
        Dimension.from_dict(payload)


def test_invalid_status() -> None:
    """Invalid status shall fail."""

    payload = create_dimension().to_dict()

    payload["status"] = "INVALID"

    with pytest.raises(ValueError):
        Dimension.from_dict(payload)


def test_dimensionless_with_nonzero_exponents() -> None:
    """
    Dimensionless quantities shall have
    zero exponents.
    """

    payload = create_dimension().to_dict()

    payload["is_dimensionless"] = True

    with pytest.raises(ValueError):
        Dimension.from_dict(payload)


def test_base_and_derived() -> None:
    """
    Base and derived flags cannot both
    be True.
    """

    payload = create_dimension().to_dict()

    payload["is_base_dimension"] = True

    with pytest.raises(ValueError):
        Dimension.from_dict(payload)

# ============================================================
# Serialization Tests
# ============================================================


def test_to_dict() -> None:
    """Verify serialization."""

    dimension = create_dimension()

    data = dimension.to_dict()

    assert isinstance(data, dict)

    assert data["dimension_id"] == "DIM-001"
    assert data["name"] == "Pressure"
    assert data["symbol"] == "[M L^-1 T^-2]"

    assert data["category"] == "DERIVED"
    assert data["physical_quantity"] == "PRESSURE"
    assert data["status"] == "ACTIVE"


def test_from_dict() -> None:
    """Verify deserialization."""

    original = create_dimension()

    reconstructed = Dimension.from_dict(
        original.to_dict()
    )

    assert reconstructed.dimension_id == original.dimension_id
    assert reconstructed.name == original.name
    assert reconstructed.symbol == original.symbol

    assert (
        reconstructed.category
        == original.category
    )

    assert (
        reconstructed.physical_quantity
        == original.physical_quantity
    )


def test_round_trip_serialization() -> None:
    """Verify deterministic round-trip serialization."""

    original = create_dimension()

    reconstructed = Dimension.from_dict(
        original.to_dict()
    )

    assert (
        reconstructed.to_dict()
        == original.to_dict()
    )


def test_reference_serialization() -> None:
    """Verify nested Reference serialization."""

    dimension = create_dimension()

    data = dimension.to_dict()

    assert isinstance(
        data["source_reference"],
        dict,
    )

    reconstructed = Dimension.from_dict(data)

    assert reconstructed.source_reference is not None

    assert (
        reconstructed.source_reference.reference_id
        == "REF-001"
    )


def test_document_serialization() -> None:
    """Verify nested Document serialization."""

    dimension = create_dimension()

    data = dimension.to_dict()

    assert isinstance(
        data["source_document"],
        dict,
    )

    reconstructed = Dimension.from_dict(data)

    assert reconstructed.source_document is not None

    assert (
        reconstructed.source_document.document_id
        == "DOC-001"
    )


def test_datetime_serialization() -> None:
    """Verify datetime ISO-8601 serialization."""

    dimension = create_dimension()

    data = dimension.to_dict()

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


def test_tuple_serialization() -> None:
    """Verify tuples serialize as lists."""

    dimension = create_dimension()

    data = dimension.to_dict()

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

    assert isinstance(
        data["engineering_disciplines"],
        list,
    )

    assert isinstance(
        data["applicable_regimes"],
        list,
    )


def test_tuple_reconstruction() -> None:
    """Verify lists reconstruct as tuples."""

    reconstructed = Dimension.from_dict(
        create_dimension().to_dict()
    )

    assert isinstance(
        reconstructed.aliases,
        tuple,
    )

    assert isinstance(
        reconstructed.common_names,
        tuple,
    )

    assert isinstance(
        reconstructed.search_keywords,
        tuple,
    )

    assert isinstance(
        reconstructed.engineering_disciplines,
        tuple,
    )

    assert isinstance(
        reconstructed.applicable_regimes,
        tuple,
    )


def test_enum_reconstruction() -> None:
    """Verify enums reconstruct correctly."""

    reconstructed = Dimension.from_dict(
        create_dimension().to_dict()
    )

    assert isinstance(
        reconstructed.category,
        DimensionCategory,
    )

    assert isinstance(
        reconstructed.physical_quantity,
        PhysicalQuantity,
    )

    assert isinstance(
        reconstructed.status,
        DimensionStatus,
    )

    assert isinstance(
        reconstructed.engineering_domain,
        EngineeringDomain,
    )


def test_copy() -> None:
    """Verify copy()."""

    dimension = create_dimension()

    copied = dimension.copy()

    assert copied == dimension

    assert copied is not dimension


def test_serialize_alias() -> None:
    """Verify serialize() delegates to to_dict()."""

    dimension = create_dimension()

    assert (
        dimension.serialize()
        == dimension.to_dict()
    )


def test_deserialize_alias() -> None:
    """Verify deserialize() delegates to from_dict()."""

    dimension = create_dimension()

    reconstructed = Dimension.deserialize(
        dimension.serialize()
    )

    assert reconstructed == dimension


def test_iter() -> None:
    """Verify __iter__()."""

    dimension = create_dimension()

    items = dict(iter(dimension))

    assert (
        items["dimension_id"]
        == "DIM-001"
    )

    assert (
        items["name"]
        == "Pressure"
    )


def test_len() -> None:
    """Verify __len__()."""

    dimension = create_dimension()

    assert len(dimension) == len(
        dimension.to_dict()
    )

# ============================================================
# Query Methods & Object Semantics
# ============================================================


def test_display_name() -> None:
    """Verify display_name()."""

    dimension = create_dimension()

    assert (
        dimension.display_name()
        == "Pressure ([M L^-1 T^-2])"
    )


def test_matches_alias() -> None:
    """Verify alias matching."""

    dimension = create_dimension()

    assert dimension.matches_alias("pressure")
    assert dimension.matches_alias("PRESSURE")
    assert not dimension.matches_alias("velocity")


def test_matches_keyword() -> None:
    """Verify keyword matching."""

    dimension = create_dimension()

    assert dimension.matches_keyword("pressure")
    assert dimension.matches_keyword("stress")
    assert not dimension.matches_keyword("rocket")


def test_has_reference() -> None:
    """Verify reference detection."""

    dimension = create_dimension()

    assert dimension.has_reference()


def test_has_document() -> None:
    """Verify document detection."""

    dimension = create_dimension()

    assert dimension.has_document()


def test_is_base() -> None:
    """Verify base dimension detection."""

    dimension = create_dimension()

    assert not dimension.is_base()


def test_is_derived() -> None:
    """Verify derived dimension detection."""

    dimension = create_dimension()

    assert dimension.is_derived()


def test_is_dimensionless_quantity() -> None:
    """Verify dimensionless detection."""

    dimension = create_dimension()

    assert not dimension.is_dimensionless_quantity()


# ============================================================
# Analysis Methods
# ============================================================


def test_base_dimension_count() -> None:
    """Verify exponent counting."""

    dimension = create_dimension()

    assert (
        dimension.base_dimension_count()
        == 3
    )


def test_nonzero_exponent_count() -> None:
    """Verify non-zero exponent counting."""

    dimension = create_dimension()

    assert (
        dimension.nonzero_exponent_count()
        == 3
    )


def test_relationship_count() -> None:
    """Verify relationship counting."""

    dimension = create_dimension()

    assert (
        dimension.relationship_count()
        == 0
    )


def test_engineering_discipline_count() -> None:
    """Verify discipline counting."""

    dimension = create_dimension()

    assert (
        dimension.engineering_discipline_count()
        == 1
    )


def test_applicable_regime_count() -> None:
    """Verify regime counting."""

    dimension = create_dimension()

    assert (
        dimension.applicable_regime_count()
        == 1
    )


def test_knowledge_tag_count() -> None:
    """Verify tag counting."""

    dimension = create_dimension()

    assert (
        dimension.knowledge_tag_count()
        == 0
    )


def test_alias_count() -> None:
    """Verify alias counting."""

    dimension = create_dimension()

    assert (
        dimension.alias_count()
        == 1
    )


def test_common_name_count() -> None:
    """Verify common-name counting."""

    dimension = create_dimension()

    assert (
        dimension.common_name_count()
        == 1
    )


def test_keyword_count() -> None:
    """Verify keyword counting."""

    dimension = create_dimension()

    assert (
        dimension.keyword_count()
        == 2
    )


def test_export_identifier_count() -> None:
    """Verify exported identifier counting."""

    dimension = create_dimension()

    assert (
        dimension.export_identifier_count()
        == 1
    )


def test_exponent_vector() -> None:
    """Verify exponent vector."""

    dimension = create_dimension()

    assert (
        dimension.exponent_vector()
        ==
        (
            -1,
            1,
            -2,
            0,
            0,
            0,
            0,
        )
    )


# ============================================================
# Object Semantics
# ============================================================


def test_immutable() -> None:
    """Verify immutability."""

    from dataclasses import FrozenInstanceError

    dimension = create_dimension()

    with pytest.raises(
        (
            FrozenInstanceError,
            AttributeError,
        )
    ):
        dimension.name = "Modified"  # type: ignore[misc]


def test_dimension_equality() -> None:
    """Verify equality after deterministic round-trip reconstruction"""

    first = create_dimension()

    second = Dimension.from_dict(first.to_dict())

    assert first == second


def test_dimension_hashable() -> None:
    """
    Verify hashability.

    NOTE:
    Enable this test after Reference and Document
    become fully hashable.
    """

    pytest.skip(
        "Reference/Document hashability "
        "not implemented yet."
    )


def test_deterministic_serialization() -> None:
    """Verify deterministic serialization."""

    dimension = create_dimension()

    assert (
        dimension.to_dict()
        ==
        dimension.to_dict()
    )


def test_round_trip_identity() -> None:
    """Verify round-trip identity."""

    original = create_dimension()

    reconstructed = Dimension.from_dict(
        original.to_dict()
    )

    assert (
        reconstructed.to_dict()
        ==
        original.to_dict()
    )            