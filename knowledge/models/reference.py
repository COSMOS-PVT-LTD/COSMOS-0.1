"""
COSMOS Knowledge Foundation

Module:
    knowledge.models.reference

Purpose:
    Canonical engineering reference model used throughout
    the COSMOS Knowledge Foundation.

Responsibilities:
    - Source traceability
    - Metadata validation
    - Citation generation
    - Serialization
    - Audit support

Author:
    COSMOS Development Team

Version:
    0.1.0
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any
from urllib.parse import urlparse


_DOI_PATTERN = re.compile(
    r"^10\.\d{4,9}/[-._;()/:A-Z0-9]+$",
    re.IGNORECASE,
)


class ReferenceType(Enum):
    """
    Engineering reference source classification.

    REQ-KF-REF-004
    """

    BOOK = "BOOK"
    NASA_REPORT = "NASA_REPORT"
    NIST_REPORT = "NIST_REPORT"
    JOURNAL = "JOURNAL"
    CONFERENCE = "CONFERENCE"
    STANDARD = "STANDARD"
    INTERNAL_DOCUMENT = "INTERNAL_DOCUMENT"
    THESIS = "THESIS"
    WEBSITE = "WEBSITE"
    OTHER = "OTHER"


class ReferenceStatus(Enum):
    """
    Lifecycle state of a reference.

    REQ-KF-REF-005
    """

    DRAFT = "DRAFT"
    APPROVED = "APPROVED"
    DEPRECATED = "DEPRECATED"
    ARCHIVED = "ARCHIVED"


@dataclass(
    frozen=True,
    slots=True,
    kw_only=True,
)
class Reference:
    """
    Canonical engineering reference model.

    Requirements Traceability:
        REQ-KF-REF-001:
            Reference objects shall be immutable.

        REQ-KF-REF-002:
            Reference objects shall support serialization.

        REQ-KF-REF-003:
            Reference objects shall validate metadata.

        REQ-KF-REF-004:
            Reference objects shall provide source traceability.

    Invariants:
        - Object remains immutable.
        - Object remains valid after construction.
        - Source metadata remains consistent.
    """

    reference_id: str
    title: str
    authors: tuple[str, ...]
    reference_type: ReferenceType

    publisher: str | None = None
    publication_year: int | None = None
    edition: str | None = None
    isbn: str | None = None
    doi: str | None = None
    url: str | None = None
    notes: str | None = None

    status: ReferenceStatus = ReferenceStatus.APPROVED

    def __post_init__(self) -> None:
        """
        Validate object immediately after creation.

        Preconditions:
            Object constructed.

        Postconditions:
            Object validated.

        Invariants:
            Object remains valid.
        """
        self.validate()

    def validate(self) -> None:
        """
        Validate all fields.

        Raises:
            ValueError:
                If any field is invalid.

        Requirements:
            REQ-KF-REF-003
        """
        if not self.reference_id.strip():
            raise ValueError(
                "reference_id must not be blank."
            )

        if not self.title.strip():
            raise ValueError(
                "title must not be blank."
            )

        if not self.authors:
            raise ValueError(
                "authors must contain at least one author."
            )

        for author in self.authors:
            if not author.strip():
                raise ValueError(
                    "author names must not be blank."
                )

        if self.publication_year is not None:
            self._validate_publication_year(
                self.publication_year
            )

        if self.doi is not None:
            self._validate_doi(self.doi)

        if self.url is not None:
            self._validate_url(self.url)

    @staticmethod
    def _validate_publication_year(
        year: int,
    ) -> None:
        """
        Validate publication year.
        """
        current_year = datetime.now().year

        if not (
            1800 <= year <= current_year + 1
        ):
            raise ValueError(
                f"Invalid publication year: {year}"
            )

    @staticmethod
    def _validate_doi(
        doi: str,
    ) -> None:
        """
        Validate DOI.
        """
        if not _DOI_PATTERN.match(doi):
            raise ValueError(
                f"Invalid DOI format: '{doi}'"
            )

    @staticmethod
    def _validate_url(
        url: str,
    ) -> None:
        """
        Validate URL.
        """
        parsed = urlparse(url)

        if not parsed.scheme or not parsed.netloc:
            raise ValueError(
                f"Invalid URL: '{url}'"
            )

    def to_dict(self) -> dict[str, Any]:
        """
        Serialize to dictionary.

        Returns:
            JSON-compatible dictionary.

        Requirements:
            REQ-KF-REF-002
        """
        return {
            "reference_id": self.reference_id,
            "title": self.title,
            "authors": list(self.authors),
            "reference_type": self.reference_type.value,
            "publisher": self.publisher,
            "publication_year": self.publication_year,
            "edition": self.edition,
            "isbn": self.isbn,
            "doi": self.doi,
            "url": self.url,
            "notes": self.notes,
            "status": self.status.value,
        }

    @classmethod
    def from_dict(
        cls,
        data: dict[str, Any],
    ) -> "Reference":
        """
        Construct Reference from dictionary.

        Args:
            data:
                Serialized payload.

        Returns:
            Reference instance.

        Raises:
            TypeError
            ValueError
        """
        if not isinstance(data, dict):
            raise TypeError(
                "data must be a dictionary."
            )

        required_fields = (
            "reference_id",
            "title",
            "authors",
            "reference_type",
        )

        missing = [
            field
            for field in required_fields
            if field not in data
        ]

        if missing:
            raise ValueError(
                f"Missing required fields: {missing}"
            )

        try:
            return cls(
                reference_id=data["reference_id"],
                title=data["title"],
                authors=tuple(data["authors"]),
                reference_type=ReferenceType(
                    data["reference_type"]
                ),
                publisher=data.get("publisher"),
                publication_year=data.get(
                    "publication_year"
                ),
                edition=data.get("edition"),
                isbn=data.get("isbn"),
                doi=data.get("doi"),
                url=data.get("url"),
                notes=data.get("notes"),
                status=ReferenceStatus(
                    data.get(
                        "status",
                        ReferenceStatus.APPROVED.value,
                    )
                ),
            )
        except KeyError as exc:
            raise ValueError(
                f"Malformed reference data: {exc}"
            ) from exc

    def citation(self) -> str:
        """
        Generate full citation.

        Returns:
            Formatted citation string.
        """
        components: list[str] = []

        if self.authors:
            components.append(
                ", ".join(self.authors)
            )

        components.append(self.title)

        if self.edition:
            components.append(self.edition)

        if self.publisher:
            components.append(self.publisher)

        if self.publication_year:
            components.append(
                str(self.publication_year)
            )

        return ", ".join(
            part for part in components if part
        )

    def short_citation(self) -> str:
        """
        Generate compact citation.

        Returns:
            Short citation string.
        """
        if not self.authors:
            return "Unknown Author"

        first_author = (
            self.authors[0]
            .split()
            [-1]
        )

        if self.publication_year:
            return (
                f"{first_author} "
                f"({self.publication_year})"
            )

        return first_author

    def __str__(self) -> str:
        """
        Human-readable representation.
        """
        return (
            f"[{self.reference_type.value}] "
            f"{self.title}"
        )