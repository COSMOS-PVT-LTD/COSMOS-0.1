"""
Unit tests for knowledge.models.variable.
"""

from __future__ import annotations

from dataclasses import FrozenInstanceError
from typing import cast

import pytest # type: ignore

from knowledge.models.document import (
    Document,
    DocumentApprovalStatus,
    DocumentType,
    SecurityLevel,
)
from knowledge.models.reference import (
    Reference,
    ReferenceStatus,
    ReferenceType,
)
from knowledge.models.variable import (
    EngineeringDomain,
    Variable,
    VariableRole,
    VariableStatus,
    VariableType,
)


def create_reference() -> Reference:
    """Create a valid Reference."""

    return Reference(
        reference_id="REF-001",
        title="Rocket Propulsion Elements",
        authors=("George P. Sutton",),
        reference_type=ReferenceType.BOOK,
        status=ReferenceStatus.APPROVED,
    )


def create_document() -> Document:
    """Create a valid Document."""

    return Document(
        document_id="DOC-001",
        document_version_id="v1",
        title="Rocket Propulsion",
        content="Rocket propulsion engineering.",
        document_type=DocumentType.MANUAL,
        reference=create_reference(),
        approval_status=DocumentApprovalStatus.DRAFT,
        security_level=SecurityLevel.INTERNAL,
    )


def create_variable() -> Variable:
    """Create a valid Variable."""

    return Variable(
        variable_id="VAR-001",
        name="Chamber Pressure",
        symbol="Pc",
        description="Combustion chamber pressure.",
        variable_type=VariableType.FLOAT,
        value=2.0e6,
        default_value=2.0e6,
        minimum_value=1.0e5,
        maximum_value=3.0e7,
        nominal_value=2.0e6,
        si_unit="Pa",
        display_unit="bar",
        dimension="Pressure",
        engineering_domain=EngineeringDomain.COMBUSTION,
        subsystem="Combustion Chamber",
        discipline="Thermodynamics",
        physical_meaning="Static chamber pressure",
        variable_role=VariableRole.INPUT,
        source_reference=create_reference(),
        source_document=create_document(),
        aliases=("Pc", "Chamber Pressure"),
        common_names=("Combustion Pressure",),
        search_keywords=("pressure", "rocket"),
        status=VariableStatus.APPROVED,
    )


# ==========================================================
# Construction Tests
# ==========================================================


def test_valid_variable_creation() -> None:
    """Verify successful Variable construction."""

    variable = create_variable()

    assert variable.variable_id == "VAR-001"
    assert variable.name == "Chamber Pressure"
    assert variable.symbol == "Pc"
    assert variable.variable_type is VariableType.FLOAT
    assert variable.engineering_domain is EngineeringDomain.COMBUSTION


# ==========================================================
# Validation Tests
# ==========================================================


def test_blank_variable_id() -> None:
    """Blank IDs shall be rejected."""

    with pytest.raises(ValueError):
        Variable.from_dict(
            {
                **create_variable().to_dict(),
                "variable_id": "   ",
            }
        )


def test_blank_name() -> None:
    """Blank names shall be rejected."""

    with pytest.raises(ValueError):
        Variable.from_dict(
            {
                **create_variable().to_dict(),
                "name": "",
            }
        )


def test_blank_symbol() -> None:
    """Blank symbols shall be rejected."""

    with pytest.raises(ValueError):
        Variable.from_dict(
            {
                **create_variable().to_dict(),
                "symbol": "",
            }
        )


def test_invalid_bounds() -> None:
    """Minimum value shall not exceed maximum value."""

    with pytest.raises(ValueError):
        Variable.from_dict(
            {
                **create_variable().to_dict(),
                "minimum_value": 10.0,
                "maximum_value": 5.0,
            }
        )

# ==========================================================
# Serialization Tests
# ==========================================================


def test_to_dict() -> None:
    """
    Verify Variable serialization.
    """

    variable = create_variable()

    payload = cast(dict[str, object], variable.to_dict())

    # ------------------------------------------------------
    # Identity
    # ------------------------------------------------------

    assert payload["variable_id"] == "VAR-001"
    assert payload["name"] == "Chamber Pressure"
    assert payload["symbol"] == "Pc"
    assert payload["description"] == "Combustion chamber pressure."

    # ------------------------------------------------------
    # Numerical Information
    # ------------------------------------------------------

    assert payload["variable_type"] == "FLOAT"
    assert payload["value"] == 2.0e6
    assert payload["default_value"] == 2.0e6
    assert payload["minimum_value"] == 1.0e5
    assert payload["maximum_value"] == 3.0e7
    assert payload["nominal_value"] == 2.0e6

    # ------------------------------------------------------
    # Units
    # ------------------------------------------------------

    assert payload["si_unit"] == "Pa"
    assert payload["display_unit"] == "bar"
    assert payload["dimension"] == "Pressure"

    # ------------------------------------------------------
    # Engineering Metadata
    # ------------------------------------------------------

    assert (
        payload["engineering_domain"]
        == "COMBUSTION"
    )

    assert (
        payload["subsystem"]
        == "Combustion Chamber"
    )

    assert (
        payload["discipline"]
        == "Thermodynamics"
    )

    # ------------------------------------------------------
    # Solver Metadata
    # ------------------------------------------------------

    assert (
        payload["variable_role"]
        == "INPUT"
    )

    # ------------------------------------------------------
    # Nested Objects
    # ------------------------------------------------------

    source_reference = cast(
        dict[str, object],
        payload["source_reference"],
    )
    assert (
        source_reference["reference_id"]
        == "REF-001"
    )

    source_document = cast(
        dict[str, object],
        payload["source_document"],
    )
    assert (
        source_document["document_id"]
        == "DOC-001"
    )

    # ------------------------------------------------------
    # AI Metadata
    # ------------------------------------------------------

    assert payload["aliases"] == [
        "Pc",
        "Chamber Pressure",
    ]

    assert payload["common_names"] == [
        "Combustion Pressure",
    ]

    assert payload["search_keywords"] == [
        "pressure",
        "rocket",
    ]

    # ------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------

    assert payload["status"] == "APPROVED"


# ==========================================================
# Deserialization Tests
# ==========================================================


def test_from_dict() -> None:
    """
    Verify Variable deserialization.
    """

    original = create_variable()

    restored = Variable.from_dict(
        original.to_dict()
    )

    assert restored == original


# ==========================================================
# Round-Trip Tests
# ==========================================================


def test_round_trip_serialization() -> None:
    """
    Verify repeated serialization remains
    deterministic.
    """

    variable = create_variable()

    first = variable.to_dict()

    second = Variable.from_dict(
        first
    ).to_dict()

    assert first == second


def test_reference_round_trip() -> None:
    """
    Verify nested Reference serialization.
    """

    variable = create_variable()

    restored = Variable.from_dict(
        variable.to_dict()
    )

    assert (
        restored.source_reference
        == variable.source_reference
    )


def test_document_round_trip() -> None:
    """
    Verify nested Document serialization.
    """

    variable = create_variable()

    restored = Variable.from_dict(
        variable.to_dict()
    )

    assert (
        restored.source_document
        == variable.source_document
    )


def test_optional_fields_round_trip() -> None:
    """
    Verify optional fields survive
    serialization.
    """

    variable = Variable(
        variable_id="VAR-002",
        name="Temperature",
        symbol="T",
        description="Gas temperature",
        variable_type=VariableType.FLOAT,
        si_unit="K",
        dimension="Temperature",
        engineering_domain=EngineeringDomain.THERMODYNAMICS,
    )

    restored = Variable.from_dict(
        variable.to_dict()
    )

    assert restored == variable        

# ==========================================================
# Query Method Tests
# ==========================================================


def test_has_value() -> None:
    """Verify has_value()."""

    variable = create_variable()

    assert variable.has_value() is True

    variable_without_value = Variable(
        variable_id="VAR-003",
        name="Density",
        symbol="rho",
        description="Fluid density",
        variable_type=VariableType.FLOAT,
        si_unit="kg/m^3",
        dimension="Density",
        engineering_domain=EngineeringDomain.FLUID_MECHANICS,
    )

    assert variable_without_value.has_value() is False


def test_is_numeric() -> None:
    """Verify is_numeric()."""

    assert create_variable().is_numeric() is True

    text_variable = Variable(
        variable_id="VAR-004",
        name="Fuel Name",
        symbol="fuel",
        description="Fuel identifier",
        variable_type=VariableType.STRING,
        si_unit="-",
        dimension="Text",
        engineering_domain=EngineeringDomain.OTHER,
    )

    assert text_variable.is_numeric() is False


def test_is_required() -> None:
    """Verify is_required()."""

    assert create_variable().is_required() is True

    optional_variable = Variable(
        variable_id="VAR-005",
        name="Comment",
        symbol="comment",
        description="Optional note",
        variable_type=VariableType.STRING,
        si_unit="-",
        dimension="Text",
        engineering_domain=EngineeringDomain.OTHER,
        required=False,
    )

    assert optional_variable.is_required() is False


def test_is_input_variable() -> None:
    """Verify is_input_variable()."""

    assert create_variable().is_input_variable() is True


def test_is_output_variable() -> None:
    """Verify is_output_variable()."""

    output_variable = Variable(
        variable_id="VAR-006",
        name="Thrust",
        symbol="F",
        description="Engine thrust",
        variable_type=VariableType.FLOAT,
        si_unit="N",
        dimension="Force",
        engineering_domain=EngineeringDomain.COMBUSTION,
        variable_role=VariableRole.OUTPUT,
    )

    assert output_variable.is_output_variable() is True
    assert output_variable.is_input_variable() is False


def test_uses_si_units() -> None:
    """Verify uses_si_units()."""

    variable = Variable(
        variable_id="VAR-007",
        name="Pressure",
        symbol="P",
        description="Pressure",
        variable_type=VariableType.FLOAT,
        si_unit="Pa",
        display_unit="Pa",
        dimension="Pressure",
        engineering_domain=EngineeringDomain.FLUID_MECHANICS,
    )

    assert variable.uses_si_units() is True

    display_variable = create_variable()

    assert display_variable.uses_si_units() is False


def test_matches_alias() -> None:
    """Verify matches_alias()."""

    variable = create_variable()

    assert variable.matches_alias("Pc")
    assert variable.matches_alias("pc")
    assert variable.matches_alias("CHAMBER PRESSURE")

    assert not variable.matches_alias("Temperature")


def test_matches_keyword() -> None:
    """Verify matches_keyword()."""

    variable = create_variable()

    assert variable.matches_keyword("pressure")
    assert variable.matches_keyword("PRESSURE")
    assert variable.matches_keyword("rocket")

    assert not variable.matches_keyword("oxygen")


def test_display_name() -> None:
    """Verify display_name()."""

    variable = create_variable()

    assert (
        variable.display_name()
        == "Chamber Pressure (Pc)"
    )


# ==========================================================
# Immutability Tests
# ==========================================================


def test_variable_is_immutable() -> None:
    """Verify Variable is immutable."""

    variable = create_variable()

    with pytest.raises(FrozenInstanceError):
        variable.name = "Modified Variable"  # type: ignore[misc]


# ==========================================================
# Equality Tests
# ==========================================================


def test_variable_equality() -> None:
    """Verify equality semantics."""

    variable_1 = create_variable()

    variable_2 = Variable.from_dict(
        variable_1.to_dict()
    )

    assert variable_1 == variable_2


def test_variable_inequality() -> None:
    """Verify inequality semantics."""

    variable_1 = create_variable()

    variable_2 = Variable.from_dict(
        {
            **variable_1.to_dict(),
            "variable_id": "VAR-999",
        }
    )

    assert variable_1 != variable_2


# ==========================================================
# Hashability Tests
# ==========================================================


#def test_variable_hashable() -> None:
  #  """Verify Variable is hashable."""

   # variable = create_variable()

   # variable_set = {variable}

   # assert variable in variable_set 


# ==========================================================
# Representation Tests
# ==========================================================


def test_string_representation() -> None:
    """
    Verify string representation exists.

    This test intentionally avoids checking the exact
    formatting so that future improvements to __str__()
    do not require test modifications.
    """

    variable = create_variable()

    assert isinstance(str(variable), str)

    assert variable.name in str(variable)    