"""
COSMOS Knowledge Foundation

Module:
    knowledge.ingestion.base

Purpose:
    Storage-neutral ingestion adapter contracts.
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from knowledge.ingestion.exceptions import IngestionAdapterError
from knowledge.ingestion.models import (
    IngestionArtifactRef,
    IngestionRequest,
    IngestionResult,
    SourceFormat,
)

__all__ = (
    "IngestionAdapter",
    "supports_source_format",
    "validate_adapter_request",
)


@runtime_checkable
class IngestionAdapter(Protocol):
    """
    Contract for document-format ingestion adapters.

    Adapters normalize registered source artifacts. They must not perform
    bulk corpus ingestion or filesystem scanning in KG-008.
    """

    @property
    def adapter_name(self) -> str:
        """Return the adapter identifier."""

    @property
    def adapter_version(self) -> str:
        """Return the adapter version string."""

    @property
    def supported_formats(self) -> frozenset[SourceFormat]:
        """Return supported source formats."""

    def can_ingest(self, artifact: IngestionArtifactRef) -> bool:
        """Return True when this adapter can ingest the artifact."""

    def ingest(self, request: IngestionRequest) -> IngestionResult:
        """
        Normalize a source artifact.

        Raises
        ------
        IngestionAdapterError
            If ingestion fails.
        """


def supports_source_format(
    adapter: IngestionAdapter,
    source_format: SourceFormat,
) -> bool:
    """Return True when an adapter declares support for a source format."""

    return source_format in adapter.supported_formats


def validate_adapter_request(
    adapter: IngestionAdapter,
    request: IngestionRequest,
) -> None:
    """
    Verify that a request is compatible with an adapter.

    Raises
    ------
    IngestionAdapterError
        If the adapter cannot process the request artifact.
    """

    if request.adapter_name != adapter.adapter_name:
        raise IngestionAdapterError(
            "Ingestion request adapter_name does not match adapter."
        )

    if not adapter.can_ingest(request.artifact):
        raise IngestionAdapterError(
            "Adapter does not support the requested artifact format."
        )
