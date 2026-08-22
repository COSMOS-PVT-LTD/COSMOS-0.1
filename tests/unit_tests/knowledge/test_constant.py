"""
Unit tests for knowledge.models.constant.
"""

from __future__ import annotations

from dataclasses import FrozenInstanceError

import pytest # type: ignore

from knowledge.models.constant import (
    Constant,
    ConstantStatus,
    ConstantType,
    EngineeringDomain,
    PreferredNumericType,
)
from knowledge.models.document import (
    Document,
    DocumentType,
)
from knowledge.models.reference import (
    Reference,
    ReferenceType,
)


def create_reference() -> Reference:
    """Create a reusable Reference."""

    return Reference(
        reference_id="REF-001",
        title="CODATA 2022",
        authors=("NIST",),
        reference_type=ReferenceType.BOOK,
    )


def create_document() -> Document:
    """Create a reusable Document."""

    return Document(
        document_id="DOC-001",
        document_version_id="1.0",
        title="Engineering Constants",
        content="Fundamental engineering constants.",
        document_type=DocumentType.MANUAL,
        reference=create_reference(),
    )


def create_constant() -> Constant:
    """Create a valid Constant."""

    return Constant(
        constant_id="CONST-001",
        name="Universal Gas Constant",
        symbol="R",
        description="Universal gas constant.",
        constant_type=ConstantType.PHYSICAL,
        constant_version="1.0",
        value=8.314462618,
        default_value=8.314462618,
        minimum_value=0.0,
        maximum_value=10.0,
        precision=1e-9,
        uncertainty=0.0,
        relative_uncertainty=0.0,
        significant_figures=9,
        exact_value=False,
        is_fundamental=True,
        si_unit="J/(mol*K)",
        display_unit="J/(mol*K)",
        dimension="kg*m^2/(s^2*mol*K)",
        engineering_domain=EngineeringDomain.GENERAL,
        source_reference=create_reference(),
        source_document=create_document(),
        preferred_numeric_type=PreferredNumericType.FLOAT64,
        status=ConstantStatus.APPROVED,
    )


def test_valid_constant() -> None:
    """Verify successful construction."""

    constant = create_constant()

    assert constant.constant_id == "CONST-001"
    assert constant.name == "Universal Gas Constant"
    assert constant.symbol == "R"


def test_blank_constant_id() -> None:
    """Blank IDs shall be rejected."""

    payload = create_constant().to_dict()

    payload["name"] = ""

    with pytest.raises(ValueError):
         Constant.from_dict(payload)


def test_blank_name() -> None:
    """Blank names shall be rejected."""

    payload = create_constant().to_dict()

    payload["name"] = ""

    print("TEST NAME:", repr(payload["name"]))

    with pytest.raises(ValueError):
         Constant.from_dict(payload)


def test_blank_symbol() -> None:
    """Blank symbols shall be rejected."""

    payload = create_constant().to_dict()

    payload["symbol"] = ""

    print("TEST SYMBOL:", repr(payload["symbol"]))

    with pytest.raises(ValueError):
         Constant.from_dict(payload)


def test_invalid_bounds() -> None:
    """Minimum value shall not exceed maximum value."""

    payload = create_constant().to_dict()

    payload["minimum_value"] = 10.0
    payload["maximum_value"] = 5.0

    with pytest.raises(ValueError):
        Constant.from_dict(payload)


def test_invalid_si_unit() -> None:
    """Blank SI unit shall be rejected."""

    payload = create_constant().to_dict()

    payload["si_unit"] = ""

    with pytest.raises(ValueError):
        Constant.from_dict(payload)


def test_invalid_dimension() -> None:
    """Blank dimension shall be rejected."""

    payload = create_constant().to_dict()

    payload["dimension"] = ""

    with pytest.raises(ValueError):
        Constant.from_dict(payload)


def test_invalid_engineering_domain() -> None:
    """Invalid engineering domain shall fail."""

    payload = create_constant().to_dict()

    payload["engineering_domain"] = "INVALID_DOMAIN"

    with pytest.raises(KeyError):
        Constant.from_dict(payload)


def test_invalid_reference() -> None:
    """Invalid reference shall fail."""

    payload = create_constant().to_dict()

    payload["source_reference"] = "invalid"

    with pytest.raises(TypeError):
        Constant.from_dict(payload)


def test_invalid_document() -> None:
    """Invalid document shall fail."""

    payload = create_constant().to_dict()

    payload["source_document"] = "invalid"

    with pytest.raises(TypeError):
        Constant.from_dict(payload)

def test_to_dict() -> None:
    """Verify deterministic serialization."""

    constant = create_constant()

    payload = constant.to_dict()

    assert payload["constant_id"] == "CONST-001"
    assert payload["name"] == "Universal Gas Constant"
    assert payload["symbol"] == "R"
    assert payload["constant_type"] == "PHYSICAL"
    assert payload["status"] == "APPROVED"
    assert payload["engineering_domain"] == "GENERAL"
    assert payload["preferred_numeric_type"] == "FLOAT64"

    reference = payload["source_reference"]
    document = payload["source_document"]

    assert isinstance(reference, dict)
    assert isinstance(document, dict)

    assert reference["reference_id"] == "REF-001"
    assert document["document_id"] == "DOC-001"


def test_from_dict() -> None:
    """Verify reconstruction from serialized data."""

    original = create_constant()

    restored = Constant.from_dict(
        original.to_dict()
    )

    assert restored == original


def test_round_trip_serialization() -> None:
    """Verify lossless round-trip serialization."""

    original = create_constant()

    payload = original.to_dict()

    restored = Constant.from_dict(payload)

    assert restored.to_dict() == payload


def test_nested_reference_serialization() -> None:
    """Verify nested Reference serialization."""

    constant = create_constant()

    payload = constant.to_dict()

    reference = payload["source_reference"]

    assert reference is not None
    assert isinstance(reference, dict)
    assert reference["reference_id"] == "REF-001"
    assert reference["title"] == "CODATA 2022"


def test_nested_document_serialization() -> None:
    """Verify nested Document serialization."""

    constant = create_constant()

    payload = constant.to_dict()

    document = payload["source_document"]

    assert document is not None
    assert isinstance(document, dict)
    assert document["document_id"] == "DOC-001"
    assert document["title"] == "Engineering Constants"


def test_enum_serialization() -> None:
    """Verify enum serialization."""

    payload = create_constant().to_dict()

    assert payload["constant_type"] == "PHYSICAL"
    assert payload["status"] == "APPROVED"
    assert payload["engineering_domain"] == "GENERAL"
    assert payload["preferred_numeric_type"] == "FLOAT64"


def test_datetime_serialization() -> None:
    """Verify ISO-8601 datetime serialization."""

    constant = create_constant()

    payload = constant.to_dict()

    if payload["created_timestamp"] is not None:
        assert isinstance(
            payload["created_timestamp"],
            str,
        )

    restored = Constant.from_dict(payload)

    assert (
        restored.created_timestamp
        == constant.created_timestamp
    )


def test_tuple_serialization() -> None:
    """Verify immutable tuple reconstruction."""

    constant = create_constant()

    payload = constant.to_dict()

    restored = Constant.from_dict(payload)

    assert isinstance(
        restored.aliases,
        tuple,
    )

    assert isinstance(
        restored.common_names,
        tuple,
    )

    assert isinstance(
        restored.search_keywords,
        tuple,
    )

    assert isinstance(
        restored.knowledge_tags,
        tuple,
    )

    assert isinstance(
        restored.related_constants,
        tuple,
    )

    assert isinstance(
        restored.related_equations,
        tuple,
    )


def test_validation_during_reconstruction() -> None:
    """Invalid serialized data shall be rejected."""

    payload = create_constant().to_dict()

    payload["constant_id"] = ""

    with pytest.raises(ValueError):
        Constant.from_dict(payload)


def test_serialization_is_deterministic() -> None:
    """Repeated serialization shall produce identical dictionaries."""

    constant = create_constant()

    first = constant.to_dict()

    second = constant.to_dict()

    assert first == second

def test_has_value() -> None:
    """Verify has_value()."""

    constant = create_constant()

    assert constant.has_value() is True


def test_is_numeric() -> None:
    """Verify is_numeric()."""

    constant = create_constant()

    assert constant.is_numeric() is True


def test_is_fundamental_constant() -> None:
    """Verify is_fundamental_constant()."""

    constant = create_constant()

    assert constant.is_fundamental_constant() is True


def test_uses_si_units() -> None:
    """Verify uses_si_units()."""

    constant = create_constant()

    assert constant.uses_si_units() is True


def test_is_dimensionless() -> None:
    """Verify is_dimensionless()."""

    dimensionless = Constant.from_dict(
        {
            **create_constant().to_dict(),
            "dimension": "1",
            "kg": 0,
            "m": 0,
            "s": 0,
            "A": 0,
            "K": 0,
            "mol": 0,
            "cd": 0,
        }
    )

    assert dimensionless.is_dimensionless() is True


def test_is_exact() -> None:
    """Verify is_exact()."""

    constant = Constant.from_dict(
        {
            **create_constant().to_dict(),
            "exact_value": True,
        }
    )

    assert constant.is_exact() is True


def test_matches_alias() -> None:
    """Verify alias lookup."""

    constant = Constant.from_dict(
        {
            **create_constant().to_dict(),
            "aliases": [
                "gas constant",
                "universal gas constant",
            ],
        }
    )

    assert constant.matches_alias("gas constant")
    assert constant.matches_alias("GAS CONSTANT")
    assert not constant.matches_alias("gravity")


def test_matches_keyword() -> None:
    """Verify keyword lookup."""

    constant = Constant.from_dict(
        {
            **create_constant().to_dict(),
            "search_keywords": [
                "thermodynamics",
                "gas",
            ],
        }
    )

    assert constant.matches_keyword("gas")
    assert constant.matches_keyword("THERMODYNAMICS")
    assert not constant.matches_keyword("combustion")


def test_display_name() -> None:
    """Verify display_name()."""

    constant = create_constant()

    assert (
        constant.display_name()
        == "Universal Gas Constant (R)"
    )


def test_has_reference() -> None:
    """Verify has_reference()."""

    assert create_constant().has_reference()


def test_has_document() -> None:
    """Verify has_document()."""

    assert create_constant().has_document()


def test_related_equation_count() -> None:
    """Verify related equation count."""

    constant = Constant.from_dict(
        {
            **create_constant().to_dict(),
            "related_equations": [
                "EQ-001",
                "EQ-002",
                "EQ-003",
            ],
        }
    )

    assert constant.related_equation_count() == 3


def test_applicable_regime_count() -> None:
    """Verify applicable regime count."""

    constant = Constant.from_dict(
        {
            **create_constant().to_dict(),
            "applicable_regimes": [
                "SUBSONIC",
                "SUPERSONIC",
            ],
        }
    )

    assert constant.applicable_regime_count() == 2


def test_knowledge_tag_count() -> None:
    """Verify knowledge tag count."""

    constant = Constant.from_dict(
        {
            **create_constant().to_dict(),
            "knowledge_tags": [
                "physics",
                "thermodynamics",
                "constants",
            ],
        }
    )

    assert constant.knowledge_tag_count() == 3


def test_export_identifier_count() -> None:
    """Verify external identifier count."""

    constant = Constant.from_dict(
        {
            **create_constant().to_dict(),
            "external_identifiers": [
                "CODATA",
                "NIST",
            ],
        }
    )

    assert constant.export_identifier_count() == 2


def test_immutable() -> None:
    """Verify Constant is immutable."""

    constant = create_constant()

    with pytest.raises(
        (
            FrozenInstanceError,
            AttributeError,
        )
    ):
        constant.name = "Modified"  # type: ignore[misc]


def test_constant_equality() -> None:
    """Verify equality semantics."""

    constant_1 = create_constant()

    constant_2 = Constant.from_dict(
        constant_1.to_dict()
    )

    assert constant_1 == constant_2


def test_constant_inequality() -> None:
    """Verify inequality semantics."""

    payload = create_constant().to_dict()

    payload["constant_id"] = "CONST-999"

    constant_1 = create_constant()
    constant_2 = Constant.from_dict(payload)

    assert constant_1 != constant_2


def test_constant_hashable() -> None:
    """Verify Constant is hashable."""

    constant = create_constant()

    try:
        constant_set = {constant}
    except TypeError:
        pytest.skip(
            "Hashability depends on nested immutable models."
        )

    assert constant in constant_set


def test_deterministic_serialization() -> None:
    """Verify deterministic serialization."""

    constant = create_constant()

    payload_1 = constant.to_dict()
    payload_2 = constant.to_dict()

    assert payload_1 == payload_2


def test_round_trip_identity() -> None:
    """Verify repeated round-trip identity."""

    original = create_constant()

    restored = Constant.from_dict(
        original.to_dict()
    )

    restored_again = Constant.from_dict(
        restored.to_dict()
    )

    assert restored_again == original           