"""
COSMOS Knowledge Foundation

Module:
    knowledge.parsers.base

Purpose:
    Document parser protocol contracts.
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from knowledge.ingestion.models import IngestionResult
from knowledge.parsers.models import NormalizedParsedDocument

__all__ = (
    "DocumentParser",
)


@runtime_checkable
class DocumentParser(Protocol):
    """
    Contract for normalizing ingested artifacts into parsed document structure.

    Parsers operate on ingestion results and do not perform filesystem access
    in KG-009 contract batches.
    """

    @property
    def parser_name(self) -> str:
        """Return the parser identifier."""

    @property
    def parser_version(self) -> str:
        """Return the parser version string."""

    def parse(self, ingestion_result: IngestionResult) -> NormalizedParsedDocument:
        """Parse an ingestion result into a normalized document structure."""
