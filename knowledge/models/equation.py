"""
COSMOS Knowledge Foundation

Module:
    knowledge.models.equation

Purpose:
    Defines the canonical engineering Equation model used
    throughout the COSMOS Knowledge Foundation.

Description:
    The Equation model represents immutable engineering
    equations together with their mathematical representation,
    provenance, engineering metadata, and validation state.

Responsibilities:
    - Mathematical representation
    - Engineering traceability
    - Metadata management
    - Serialization
    - Validation
    - Future symbolic integration

Author:
    COSMOS Development Team

Version:
    0.1.0
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any

from knowledge.models.document import Document
from knowledge.models.reference import Reference

class EquationCategory(Enum):
    """
    Engineering equation classification.
    """

    THERMODYNAMICS = "THERMODYNAMICS"

    FLUID_DYNAMICS = "FLUID_DYNAMICS"

    GAS_DYNAMICS = "GAS_DYNAMICS"

    COMBUSTION = "COMBUSTION"

    HEAT_TRANSFER = "HEAT_TRANSFER"

    CRYOGENICS = "CRYOGENICS"

    MATERIALS = "MATERIALS"

    STRUCTURES = "STRUCTURES"

    OPTIMIZATION = "OPTIMIZATION"

    RELIABILITY = "RELIABILITY"

    OTHER = "OTHER"

class EquationStatus(Enum):
    """
    Equation lifecycle status.
    """

    DRAFT = "DRAFT"

    VERIFIED = "VERIFIED"

    APPROVED = "APPROVED"

    DEPRECATED = "DEPRECATED"

@dataclass(
    frozen=True,
    slots=True,
    kw_only=True,
)
class Equation:
    equation_id: str

    equation_name: str

    equation_category: EquationCategory

    equation_version: str

    source_document: Document

    source_reference: Reference

    expression: str

    latex_expression: str

    symbolic_expression: str

    normalized_expression: str | None = None

    chapter: str | None = None

    section: str | None = None

    subsection: str | None = None

    page_number: int | None = None

    figure_number: str | None = None

    table_number: str | None = None

    paragraph_number: str | None = None

    extracted_by: str | None = None

    extraction_confidence: float | None = None

    status: EquationStatus = EquationStatus.DRAFT

    def __post_init__(
        self,
    ) -> None:
        """
        Validate the Equation immediately after construction.

        An Equation object shall never exist in an invalid state.
        """

        self.validate()

    def validate(
        self,
    ) -> None:
        """
        Validate the Equation.

        Raises
        ------
        ValueError
            If any field is invalid.
        """

        self._validate_equation_id()

        self._validate_equation_name()

        self._validate_expression()

        self._validate_document()

        self._validate_reference()

        self._validate_page_number()

        self._validate_extraction_confidence()

    def _validate_equation_id(
        self,
    ) -> None:
        """
        Validate the equation identifier.
        """

        if not isinstance(self.equation_id, str) or not self.equation_id.strip():
            raise ValueError("equation_id must be a non-blank string.")

    def _validate_equation_name(self) -> None:
        if not isinstance(self.equation_name, str) or not self.equation_name.strip():
            raise ValueError("equation_name must be a non-blank string.")

    def _validate_expression(self) -> None:
        if not isinstance(self.expression, str) or not self.expression.strip():
            raise ValueError("expression must be a non-blank string.")

    def _validate_document(self) -> None:
        if not isinstance(self.source_document, Document):
            raise ValueError("source_document must be a Document instance.")

    def _validate_reference(self) -> None:
        if not isinstance(self.source_reference, Reference):
            raise ValueError("source_reference must be a Reference instance.")

    def _validate_page_number(self) -> None:
        if self.page_number is not None:
            if not isinstance(self.page_number, int) or self.page_number <= 0:
                raise ValueError("page_number must be a positive integer if provided.")

    def _validate_extraction_confidence(self) -> None:
        if self.extraction_confidence is not None:
            if not (isinstance(self.extraction_confidence, (int, float)) and 0.0 <= self.extraction_confidence <= 1.0):
                raise ValueError("extraction_confidence must be a number between 0.0 and 1.0 if provided.")

    def to_dict(
        self,
    ) -> dict[str, Any]:
        """
        Serialize the Equation into a deterministic dictionary.

        Returns
        -------
        dict[str, Any]
            JSON-serializable representation of the Equation.
        """

        return {
            "equation_id": self.equation_id,
            "equation_name": self.equation_name,
            "equation_category": self.equation_category.value,
            "equation_version": self.equation_version,
            "source_document": self.source_document.to_dict(),
            "source_reference": self.source_reference.to_dict(),
            "expression": self.expression,
            "latex_expression": self.latex_expression,
            "symbolic_expression": self.symbolic_expression,
            "normalized_expression": self.normalized_expression,
            "chapter": self.chapter,
            "section": self.section,
            "subsection": self.subsection,
            "page_number": self.page_number,
            "figure_number": self.figure_number,
            "table_number": self.table_number,
            "paragraph_number": self.paragraph_number,
            "extracted_by": self.extracted_by,
            "extraction_confidence": self.extraction_confidence,
            "status": self.status.value,
        }

    @classmethod
    def from_dict(
        cls,
        data: dict[str, Any],
    ) -> "Equation":
        """
        Construct an Equation from a serialized dictionary.

        Parameters
        ----------
        data : dict[str, Any]

        Returns
        -------
        Equation

        Raises
        ------
        ValueError
            If required fields are missing.
        """

        required_fields = (
            "equation_id",
            "equation_name",
            "equation_category",
            "equation_version",
            "source_document",
            "source_reference",
            "expression",
            "latex_expression",
            "symbolic_expression",
            "normalized_expression",        
        )

        missing = [
            field
            for field in required_fields
            if field not in data
        ]

        if missing:
            raise ValueError(
                "Missing required fields: "
                + ", ".join(missing)
            )

        return cls(
            equation_id=data["equation_id"],
            equation_name=data["equation_name"],
            equation_category=EquationCategory(
                data["equation_category"]
            ),
            equation_version=data["equation_version"],
            source_document=Document.from_dict(
                data["source_document"]
            ),
            source_reference=Reference.from_dict(
                data["source_reference"]
            ),
            expression=data["expression"],
            latex_expression=data["latex_expression"],
            symbolic_expression=data[
                "symbolic_expression"
            ],
            normalized_expression=data.get(
                "normalized_expression",
            ),
            chapter=data.get("chapter"),
            section=data.get("section"),
            subsection=data.get("subsection"),
            page_number=data.get("page_number"),
            figure_number=data.get("figure_number"),
            table_number=data.get("table_number"),
            paragraph_number=data.get(
                "paragraph_number"
            ),
            extracted_by=data.get(
                "extracted_by"
            ),
            extraction_confidence=data.get(
                "extraction_confidence"
            ),
            status=EquationStatus(
                data.get(
                    "status",
                    EquationStatus.DRAFT.value,
                )
            ),
        )