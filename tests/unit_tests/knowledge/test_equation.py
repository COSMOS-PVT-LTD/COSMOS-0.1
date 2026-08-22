"""
Unit tests for knowledge.models.equation.
"""

from __future__ import annotations

from dataclasses import FrozenInstanceError

import pytest  # type: ignore[import]

from knowledge.models.document import (
    Document,
    DocumentApprovalStatus,
    DocumentType,
    SecurityLevel,
)

from knowledge.models.equation import (
    Equation,
    EquationCategory,
    EquationStatus,
)

from knowledge.models.reference import (
    Reference,
    ReferenceStatus,
    ReferenceType,
)

def create_reference() -> Reference:
    """
    Create a valid Reference.
    """

    return Reference(
        reference_id="REF-001",
        title="Rocket Propulsion Elements",
        authors=("George P. Sutton",),
        reference_type=ReferenceType.BOOK,
        status=ReferenceStatus.APPROVED,
    )

def create_document() -> Document:
    """
    Create a valid Document.
    """

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

def create_equation() -> Equation:
    """
    Create a valid Equation.
    """

    return Equation(
        equation_id="EQ-001",
        equation_name="Rocket Thrust",

        equation_category=EquationCategory.COMBUSTION,

        equation_version="1.0",

        source_document=create_document(),

        source_reference=create_reference(),

        expression="F = mdot * Ve",

        latex_expression=r"F=\dot{m}V_e",

        symbolic_expression="F = mdot * Ve",

        normalized_expression="F=mdot*Ve",

        status=EquationStatus.APPROVED,
    )

def test_valid_equation_creation() -> None:
    """
    Verify successful construction.
    """

    equation = create_equation()

    assert equation.equation_id == "EQ-001"

    assert equation.equation_name == "Rocket Thrust"

    assert equation.equation_category == EquationCategory.COMBUSTION

    assert equation.equation_version == "1.0"

    assert equation.source_document.document_id == "DOC-001"

    assert equation.source_reference.reference_id == "REF-001"

    assert equation.expression == "F = mdot * Ve"   

    assert equation.latex_expression == r"F=\dot{m}V_e"

    assert equation.symbolic_expression == "F = mdot * Ve"

    assert equation.normalized_expression == "F=mdot*Ve"

    assert equation.status == EquationStatus.APPROVED

def test_blank_equation_id() -> None:

    with pytest.raises(ValueError):

        Equation(
            **{
                **create_equation().to_dict(),
                "equation_id": "   ",
            }
        )

def test_blank_equation_name() -> None:

    with pytest.raises(ValueError):

        Equation(
            **{
                **create_equation().to_dict(),
                "equation_name": "",
            }
        )

def test_blank_expression() -> None:

    with pytest.raises(ValueError):

        Equation(
            **{
                **create_equation().to_dict(),
                "expression": "",
            }
        )

def test_invalid_page_number() -> None:

    with pytest.raises(ValueError):

        Equation(
            **{
                **create_equation().to_dict(),
                "page_number": -5,
            }
        )

def test_invalid_confidence() -> None:

    with pytest.raises(ValueError):

        Equation(
            **{
                **create_equation().to_dict(),
                "extraction_confidence": 1.5,
            }
        )

def test_to_dict() -> None:

    equation = create_equation()

    payload = equation.to_dict()

    assert payload["equation_id"] == "EQ-001"

    assert payload["status"] == "APPROVED"

    assert payload["equation_name"] == "Rocket Thrust"

    assert payload["equation_category"] == "COMBUSTION"

    assert payload["equation_version"] == "1.0"

    assert payload["source_document"]["document_id"] == "DOC-001"

    assert payload["source_reference"]["reference_id"] == "REF-001"

    assert payload["expression"] == "F = mdot * Ve"

    assert payload["latex_expression"] == r"F=\dot{m}V_e"

    assert payload["symbolic_expression"] == "F = mdot * Ve"

    assert payload["normalized_expression"] == "F=mdot*Ve"

def test_from_dict() -> None:

    original = create_equation()

    restored = Equation.from_dict(
        original.to_dict()
    )

    assert restored == original

def test_immutable() -> None:
    """
    Verify that Equation is immutable.
    """

    equation = create_equation()

    with pytest.raises(FrozenInstanceError):
        equation.equation_name = "New Name"  # type: ignore[misc]

def test_traceability() -> None:

    equation = create_equation()

    assert (
        equation.source_document
        is not None
    )

    assert (
        equation.source_reference
        is not None
    )



