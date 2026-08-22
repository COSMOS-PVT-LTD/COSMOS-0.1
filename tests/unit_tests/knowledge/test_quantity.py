"""
Unit tests for knowledge.models.quantity.
"""

from __future__ import annotations

from dataclasses import FrozenInstanceError
from datetime import datetime, timezone

import pytest  # type: ignore

from knowledge.models.dimension import (
    Dimension,
    DimensionCategory,
    DimensionStatus,
    EngineeringDomain,
    PhysicalQuantity,
)
from knowledge.models.document import Document, DocumentType
from knowledge.models.quantity import (
    MeasurementType,
    Quantity,
    QuantityCategory,
    QuantityCriticality,
    QuantityStatus,
    ValueRepresentation,
)
from knowledge.models.reference import Reference, ReferenceType
from knowledge.models.unit import (
    QuantityType,
    Unit,
    UnitCategory,
    UnitStatus,
    UnitSystem,
)

FIXED_TIME = datetime(2026, 1, 1, tzinfo=timezone.utc)


def create_reference() -> Reference:
    """Create a valid Reference."""

    return Reference(
        reference_id="REF-001",
        reference_type=ReferenceType.BOOK,
        authors=("George P. Sutton",),
        title="Rocket Propulsion Elements",
        publication_year=1971,
    )


def create_document() -> Document:
    """Create a valid Document."""

    return Document(
        document_id="DOC-001",
        document_version_id="1.0",
        document_type=DocumentType.MANUAL,
        title="Rocket Propulsion",
        content="Rocket propulsion engineering handbook.",
        reference=create_reference(),
    )


def create_dimension() -> Dimension:
    """Create a valid Dimension."""

    return Dimension(
        dimension_id="DIM-001",
        name="Pressure",
        symbol="[M L^-1 T^-2]",
        description="Pressure dimension.",
        category=DimensionCategory.DERIVED,
        physical_quantity=PhysicalQuantity.PRESSURE,
        status=DimensionStatus.ACTIVE,
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
        engineering_domain=EngineeringDomain.GENERAL,
        engineering_disciplines=("Propulsion",),
        applicable_regimes=("Compressible",),
        aliases=("pressure",),
        common_names=("Pressure",),
        search_keywords=("pressure", "stress"),
        source_reference=create_reference(),
        source_document=create_document(),
        version="1.0",
        created_timestamp=FIXED_TIME,
        modified_timestamp=FIXED_TIME,
        approved_timestamp=FIXED_TIME,
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
        created_timestamp=FIXED_TIME,
        modified_timestamp=FIXED_TIME,
        created_by="COSMOS",
        approved_by="Chief Engineer",
        approved_timestamp=FIXED_TIME,
        symbolic_representation="Pa",
        canonical_symbol="Pa",
    )


def create_quantity(**overrides: object) -> Quantity:
    """Create a valid Quantity."""

    payload = {
        "quantity_id": "QTY-001",
        "name": "Chamber Pressure Value",
        "short_name": "Pc",
        "symbol": "P",
        "description": (
            "Static pressure in the combustion chamber used for "
            "propulsion performance analysis."
        ),
        "category": QuantityCategory.SCALAR,
        "measurement_type": MeasurementType.CALCULATED,
        "status": QuantityStatus.ACTIVE,
        "criticality": QuantityCriticality.HIGH,
        "value_representation": ValueRepresentation.EXACT,
        "physical_quantity_name": "Pressure Magnitude",
        "physical_quantity_symbol": "Pm",
        "value": 2.0e6,
        "unit": create_unit(),
        "dimension": create_dimension(),
        "aliases": ("Chamber Pressure",),
        "search_keywords": ("pressure", "chamber"),
        "reasoning_enabled": False,
        "calculated_value": True,
    }
    payload.update(overrides)
    return Quantity(**payload)


# ==========================================================
# Construction Tests
# ==========================================================


def test_valid_quantity_creation() -> None:
    """Verify successful Quantity construction."""

    quantity = create_quantity()

    assert quantity.quantity_id == "QTY-001"
    assert quantity.name == "Chamber Pressure Value"
    assert quantity.symbol == "P"
    assert quantity.category is QuantityCategory.SCALAR
    assert quantity.value == 2.0e6


def test_display_properties() -> None:
    """Verify display-oriented properties."""

    quantity = create_quantity()

    assert quantity.display_name == "Chamber Pressure Value"
    assert quantity.canonical_name == "Chamber Pressure Value"
    assert "P" in quantity.engineering_name


# ==========================================================
# Validation Tests
# ==========================================================


def test_blank_quantity_id() -> None:
    """Blank quantity identifiers shall be rejected."""

    with pytest.raises(ValueError):
        create_quantity(quantity_id="   ")


def test_reserved_quantity_id() -> None:
    """Reserved identifiers shall be rejected."""

    with pytest.raises(ValueError):
        create_quantity(quantity_id="UNKNOWN")


def test_name_equals_short_name() -> None:
    """short_name must differ from name."""

    with pytest.raises(ValueError):
        create_quantity(
            name="Chamber Pressure Value",
            short_name="Chamber Pressure Value",
        )


def test_symbol_equals_name() -> None:
    """symbol must differ from name."""

    with pytest.raises(ValueError):
        create_quantity(symbol="Chamber Pressure Value")


def test_missing_alias_and_keyword() -> None:
    """At least one alias or search keyword is required."""

    with pytest.raises(ValueError):
        create_quantity(aliases=(), search_keywords=())


def test_measured_exact_conflict() -> None:
    """Measured quantities cannot be classified as exact."""

    with pytest.raises(ValueError):
        create_quantity(
            measurement_type=MeasurementType.MEASURED,
            value_representation=ValueRepresentation.EXACT,
        )


def test_reasoning_requires_graph_node() -> None:
    """Reasoning-enabled quantities require a graph node identifier."""

    with pytest.raises(ValueError):
        create_quantity(reasoning_enabled=True, graph_node_id=None)


# ==========================================================
# Serialization Tests
# ==========================================================


def test_to_dict_round_trip_keys() -> None:
    """to_identity_dict shall include core identity fields."""

    quantity = create_quantity()
    payload = quantity.to_identity_dict()

    assert payload["quantity_id"] == "QTY-001"
    assert payload["name"] == "Chamber Pressure Value"
    assert payload["symbol"] == "P"


def test_from_dict_construction() -> None:
    """from_dict shall reconstruct a Quantity when given valid kwargs."""

    original = create_quantity()
    identity = original.to_identity_dict()
    restored = Quantity.from_dict(
        {
            **identity,
            "category": original.category,
            "measurement_type": original.measurement_type,
            "status": original.status,
            "criticality": original.criticality,
            "value_representation": original.value_representation,
            "physical_quantity_name": original.physical_quantity_name,
            "physical_quantity_symbol": original.physical_quantity_symbol,
            "value": original.value,
            "unit": original.unit,
            "dimension": original.dimension,
            "reasoning_enabled": False,
            "calculated_value": True,
        }
    )

    assert restored.quantity_id == original.quantity_id
    assert restored.name == original.name
    assert restored.value == original.value


# ==========================================================
# Immutability Tests
# ==========================================================


def test_quantity_is_immutable() -> None:
    """Quantity instances shall be immutable."""

    quantity = create_quantity()

    with pytest.raises(FrozenInstanceError):
        quantity.value = 3.0e6  # type: ignore[misc]


# ==========================================================
# Computed Property Tests
# ==========================================================


def test_computed_relative_uncertainty_none_without_uncertainty() -> None:
    """Computed relative uncertainty is None when uncertainty is unset."""

    quantity = create_quantity(uncertainty=None)

    assert quantity.computed_relative_uncertainty is None
