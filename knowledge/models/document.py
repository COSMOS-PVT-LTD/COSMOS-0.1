"""
COSMOS Knowledge Foundation

Module:
    knowledge.models.document

Purpose:
    Canonical engineering document model used throughout
    the COSMOS Knowledge Foundation.

Responsibilities:
    - Engineering content storage
    - Source traceability
    - Content integrity verification
    - Governance tracking
    - Validation

Author:
    COSMOS Development Team

Version:
    0.1.0
"""

from __future__ import annotations
from typing import Any, Mapping

import math
import hashlib
import re

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from types import MappingProxyType
from knowledge.models.reference import Reference


_SHA256_PATTERN = re.compile(r"^[a-fA-F0-9]{64}$")


class DocumentType(Enum):
    """
    Engineering document classification.
    """

    NASA_REPORT = "NASA_REPORT"
    NIST_REPORT = "NIST_REPORT"
    TEXTBOOK = "TEXTBOOK"
    JOURNAL = "JOURNAL"
    CONFERENCE_PAPER = "CONFERENCE_PAPER"
    STANDARD = "STANDARD"
    INTERNAL_DOCUMENT = "INTERNAL_DOCUMENT"
    DATABASE_EXPORT = "DATABASE_EXPORT"
    TECHNICAL_NOTE = "TECHNICAL_NOTE"
    MANUAL = "MANUAL"
    PATENT = "PATENT"
    THESIS = "THESIS"
    OTHER = "OTHER"
    SPECIFICATION = "SPECIFICATION"


class DocumentApprovalStatus(Enum):
    """
    Engineering review lifecycle status.
    """

    DRAFT = "DRAFT"
    UNDER_REVIEW = "UNDER_REVIEW"
    APPROVED = "APPROVED"
    DEPRECATED = "DEPRECATED"
    ARCHIVED = "ARCHIVED"


class SecurityLevel(Enum):
    """
    Document security classification.
    """

    PUBLIC = "PUBLIC"
    INTERNAL = "INTERNAL"
    CONFIDENTIAL = "CONFIDENTIAL"
    RESTRICTED = "RESTRICTED"


@dataclass(
    frozen=True,
    slots=True,
    kw_only=True,
)
class Document:
    """
    Canonical engineering document.

    Represents machine-readable engineering
    content imported into COSMOS.

    This class is intentionally limited to:

    - Identity
    - Traceability
    - Governance
    - Validation
    - Integrity Verification

    Additional capabilities such as:

    - Serialization
    - Analytics
    - Search
    - Repository Helpers

    shall be implemented in later phases.
    """

    # ------------------------------------------------------------------
    # Identity
    # ------------------------------------------------------------------

    document_id: str

    document_version_id: str

    revision_number: int = 0

    # ------------------------------------------------------------------
    # Core Content
    # ------------------------------------------------------------------

    title: str

    content: str

    document_type: DocumentType

    reference: Reference

    # ------------------------------------------------------------------
    # Repository Metadata
    # ------------------------------------------------------------------

    chapter: str | None = None

    section: str | None = None

    tags: tuple[str, ...] = ()

    metadata: Mapping[str, Any] = field(
    default_factory=lambda: MappingProxyType({})
    )

    # ------------------------------------------------------------------
    # Governance
    # ------------------------------------------------------------------

    approval_status: DocumentApprovalStatus = (
        DocumentApprovalStatus.DRAFT
    )

    security_level: SecurityLevel = (
        SecurityLevel.INTERNAL
    )

    # ------------------------------------------------------------------
    # Integrity
    # ------------------------------------------------------------------

    content_hash: str = ""

    # ------------------------------------------------------------------
    # Audit
    # ------------------------------------------------------------------

    
    import_timestamp: datetime = field(
        default_factory=lambda:
        datetime.now(timezone.utc)
)

    def __post_init__(self) -> None:
        """
        Validate document and generate
        content hash when necessary.
        """

        if not self.content_hash:
            generated_hash = self._generate_hash(
                self.content
            )

            object.__setattr__(
                self,
                "content_hash",
                generated_hash,
            )
        if not isinstance(
            self.metadata,
            MappingProxyType,
       ):
            object.__setattr__(
                self,
                "metadata",
                MappingProxyType(
                    dict(self.metadata)
            ),
        )
        self.validate()

    def validate(self) -> None:
        """
        Validate document fields.

        Raises
        ------
        ValueError
            If any field is invalid.

        TypeError
            If any object type is invalid.
        """

        if not self.document_id.strip():
            raise ValueError(
                "document_id must not be blank."
            )

        if not self.document_version_id.strip():
            raise ValueError(
                "document_version_id must not be blank."
            )

        if not self.title.strip():
            raise ValueError(
                "title must not be blank."
            )

        if not self.content.strip():
            raise ValueError(
                "content must not be blank."
            )

        if self.revision_number < 0:
            raise ValueError(
                "revision_number must be >= 0."
            )

        if not isinstance(
            self.reference,
            Reference,
        ):
            raise TypeError(
                "reference must be a Reference instance."
            )

        if not isinstance(
            self.document_type,
            DocumentType,
        ):
            raise TypeError(
                "document_type must be a "
                "DocumentType."
            )

        if not isinstance(
            self.approval_status,
            DocumentApprovalStatus,
        ):
            raise TypeError(
                "approval_status must be a "
                "DocumentApprovalStatus."
            )

        if not isinstance(
            self.security_level,
            SecurityLevel,
        ):
            raise TypeError(
                "security_level must be a "
                "SecurityLevel."
            )

        self._validate_hash(
            self.content_hash
        )

    @staticmethod
    def _generate_hash(
        content: str,
    ) -> str:
        """
        Generate SHA256 content hash.

        Parameters
        ----------
        content : str
            Document content.

        Returns
        -------
        str
            SHA256 hash.
        """

        return hashlib.sha256(
            content.encode("utf-8")
        ).hexdigest()

    @staticmethod
    def _validate_hash(
        value: str,
    ) -> None:
        """
        Validate SHA256 hash.

        Parameters
        ----------
        value : str
            Hash string.

        Raises
        ------
        ValueError
            Invalid hash.
        """

        if not _SHA256_PATTERN.match(
            value
        ):
            raise ValueError(
                "content_hash must be a valid "
                "SHA256 hexadecimal hash."
            )

    def verify_integrity(
        self,
    ) -> bool:
        """
        Verify content integrity.

        Returns
        -------
        bool
            True if stored hash matches
            current content.
        """

        return (
            self._generate_hash(
                self.content
            )
            == self.content_hash
        )
    def to_dict(self) -> dict[str, Any]:
        """
        Serialize document into a JSON-compatible
        dictionary representation.

        Returns
        -------
        dict[str, Any]
            Serialized document.
        """

        return {
            "document_id": self.document_id,
            "document_version_id": self.document_version_id,
            "revision_number": self.revision_number,
            "title": self.title,
            "content": self.content,
            "document_type": self.document_type.value,
            "reference": self.reference.to_dict(),
            "approval_status": self.approval_status.value,
            "security_level": self.security_level.value,
            "chapter": self.chapter,
            "section": self.section,
            "tags": list(self.tags),
            "metadata": dict(self.metadata),
            "content_hash": self.content_hash,
            "import_timestamp": self.import_timestamp.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Document":


        if not isinstance(
            data,
            dict,
        ):
            raise TypeError(
                "data must be a dictionary."
            )

        required_keys = (
            "document_id",
            "document_version_id",
            "title",
            "content",
            "document_type",
            "reference",
        )

        missing = [
            key
            for key in required_keys
            if key not in data
        ]

        if missing:
            raise ValueError(
                f"Missing required fields: "
                f"{missing}"
            )

        return cls(
            document_id=str(
                data["document_id"]
           ),

        document_version_id=str(
            data["document_version_id"]
        ),

        revision_number=int(
            data.get(
                "revision_number",
                0,
            )
        ),

        title=str(
            data["title"]
        ),

        content=str(
            data["content"]
        ),

        document_type=DocumentType(
            data["document_type"]
        ),

        reference=Reference.from_dict(
            data["reference"]
        ),

        chapter=data.get(
          "chapter"
        ),

        section=data.get(
           "section"
        ),

        tags=tuple(
            data.get(
              "tags",
              [],
             )
        ),

        metadata=data.get(
             "metadata",
              {},
        ),

        approval_status=
            DocumentApprovalStatus(
                data.get(
                    "approval_status",
                    DocumentApprovalStatus.DRAFT.value,
                )
            ),

        security_level=
            SecurityLevel(
                data.get(
                    "security_level",
                    SecurityLevel.INTERNAL.value,
                )
            ),

        content_hash=str(
            data.get(
                "content_hash",
                "",
            )
        ),

        import_timestamp=
            datetime.fromisoformat(
                str(
                    data.get(
                        "import_timestamp",
                        datetime.now(
                            timezone.utc
                        ).isoformat(),
                    )
                )
            ),
    )
    def word_count(
        self,
    ) -> int:
        """
        Return total word count.

        Returns
        -------
        int
            Number of words in content.
        """

        return len(
            self.content.split()
        )
    def line_count(
        self,
    ) -> int:
        """
        Return total line count.

        Returns
        -------
        int
            Number of lines.
        """

        return len(
            self.content.splitlines()
        )
    def character_count(
        self,
    ) -> int:
        """
        Return total character count.

        Returns
        -------
        int
            Number of characters.
        """

        return len(
            self.content
        )
    
    def unique_word_count(
        self,
    ) -> int:
        """
        Return count of unique words.

        Returns
        -------
        int
            Unique word count.
        """

        words = {
            word.lower()
            for word in self.content.split()
        }

        return len(words) 
    def estimated_token_count(
        self,
    ) -> int:
        """
        Estimate LLM token count.

        Uses:

        4 characters ≈ 1 token

        Returns
        -------
        int
            Estimated token count.
        """

        return math.ceil(
            len(self.content) / 4
        )
    def reading_time_minutes(
        self,
    ) -> int:
        """
        Estimate reading time.

        Assumes:

        200 words/minute

        Returns
        -------
        int
            Estimated reading time.
        """

        words = self.word_count()

        return max(
            1,
            math.ceil(words / 200),
        )
    def has_content(
        self,
    ) -> bool:
        """
        Determine whether document
        contains non-whitespace content.

        Returns
        -------
        bool
        """

        return bool(
            self.content.strip()
        )
    def summary(
        self,
        max_length: int = 250,
    ) -> str:
        """
        Generate preview summary.

        Parameters
        ----------
        max_length : int

        Returns
        -------
        str
        """

        if max_length <= 0:
            raise ValueError(
                "max_length must be > 0."
            )

        if (
            len(self.content)
            <= max_length
        ):
            return self.content

        return (
            self.content[
                : max_length - 3
            ]
            + "..."
        )

    def contains_keyword(
        self,
        keyword: str,
    ) -> bool:
        """
        Case-insensitive keyword search.

        Parameters
        ----------
        keyword : str

        Returns
        -------
        bool
        """

        if not keyword.strip():
            raise ValueError(
                "keyword must not be blank."
            )

        return (
            keyword.lower()
            in self.content.lower()
        )

    def contains_phrase(
        self,
        phrase: str,
    ) -> bool:
        """
        Case-insensitive phrase search.

        Parameters
        ----------
        phrase : str

        Returns
        -------
        bool
        """

        if not phrase.strip():
            raise ValueError(
                "phrase must not be blank."
            )

        return (
            phrase.lower()
            in self.content.lower()
        )

    def starts_with(
        self,
        text: str,
    ) -> bool:
        """
        Check whether content starts
        with specified text.

        Parameters
        ----------
        text : str

        Returns
        -------
        bool
        """

        if not text.strip():
            raise ValueError(
                "text must not be blank."
            )

        return (
            self.content.lower()
            .startswith(
                text.lower()
            )
        )

    def ends_with(
        self,
        text: str,
    ) -> bool:
        """
        Check whether content ends
        with specified text.

        Parameters
        ----------
        text : str

        Returns
        -------
        bool
        """

        if not text.strip():
            raise ValueError(
                "text must not be blank."
            )

        return (
            self.content.lower()
            .endswith(
                text.lower()
            )
        )
    def matches_regex(
        self,
        pattern: str,
    ) -> bool:
        """
        Search content using a regular
        expression.

        Parameters
        ----------
        pattern : str

        Returns
        -------
        bool
        """

        if not pattern.strip():
            raise ValueError(
                "pattern must not be blank."
            )

        return (
            re.search(
                pattern,
                self.content,
                re.IGNORECASE,
            )
            is not None
        )

    def get_metadata(
        self,
    ) -> Mapping[str, Any]:
        """
        Return document metadata.

        Returns
        -------
        Mapping[str, Any]
        """

        return self.metadata
    def get_tag_set(
        self,
    ) -> set[str]:
        """
        Return unique tags.

        Returns
        -------
        set[str]
        """

        return set(
            self.tags
        )

    def belongs_to_chapter(
        self,
        chapter: str,
    ) -> bool:
        """
        Determine whether document
        belongs to a chapter.

        Parameters
        ----------
        chapter : str

        Returns
        -------
        bool
        """

        if not chapter.strip():
            raise ValueError(
                "chapter must not be blank."
            )

        if self.chapter is None:
            return False

        return (
            self.chapter.lower()
            == chapter.lower()
        )

    def belongs_to_section(
        self,
        section: str,
    ) -> bool:
        """
        Determine whether document
        belongs to a section.

        Parameters
        ----------
        section : str

        Returns
        -------
        bool
        """

        if not section.strip():
            raise ValueError(
                "section must not be blank."
            )

        if self.section is None:
            return False

        return (
            self.section.lower()
            == section.lower()
        )

    def __str__(self) -> str:
        """
        Human-readable representation.
        """

        return (
            f"[DOCUMENT] "
            f"{self.title}"
        ) 
