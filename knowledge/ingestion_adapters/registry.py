"""Ingestion adapter registry and orchestration."""

from __future__ import annotations

from knowledge.ingestion.base import IngestionAdapter
from knowledge.ingestion.exceptions import IngestionAdapterError
from knowledge.ingestion.models import IngestionArtifactRef, IngestionRequest, IngestionResult
from knowledge.ingestion_adapters.docx import DocxIngestionAdapter
from knowledge.ingestion_adapters.html import HtmlIngestionAdapter, MarkdownIngestionAdapter
from knowledge.ingestion_adapters.pdf import PdfIngestionAdapter
from knowledge.ingestion_adapters.pptx import PptxIngestionAdapter
from knowledge.ingestion_adapters.xlsx import XlsxIngestionAdapter
from knowledge.source.vault import SourceVault

__all__ = (
    "IngestionAdapterRegistry",
    "IngestionOrchestrator",
    "build_default_registry",
)


class IngestionAdapterRegistry:
    """Deterministic adapter dispatch registry."""

    def __init__(self, adapters: tuple[IngestionAdapter, ...]) -> None:
        self._adapters = tuple(adapters)
        self._by_name = {adapter.adapter_name: adapter for adapter in adapters}

    def get(self, adapter_name: str) -> IngestionAdapter:
        try:
            return self._by_name[adapter_name]
        except KeyError as exc:
            raise IngestionAdapterError(
                f"No ingestion adapter registered with name '{adapter_name}'."
            ) from exc

    def resolve(self, artifact: IngestionArtifactRef) -> IngestionAdapter:
        matches = tuple(
            adapter
            for adapter in self._adapters
            if adapter.can_ingest(artifact)
        )

        if not matches:
            raise IngestionAdapterError(
                f"No adapter supports format '{artifact.source_format.value}'."
            )

        if len(matches) > 1:
            raise IngestionAdapterError(
                "Multiple adapters support the requested artifact format."
            )

        return matches[0]

    def adapters(self) -> tuple[IngestionAdapter, ...]:
        return self._adapters


def build_default_registry(vault: SourceVault) -> IngestionAdapterRegistry:
    """Build the default BLOCK-005 adapter registry."""

    adapters: tuple[IngestionAdapter, ...] = (
        PdfIngestionAdapter(vault),
        DocxIngestionAdapter(vault),
        PptxIngestionAdapter(vault),
        XlsxIngestionAdapter(vault),
        HtmlIngestionAdapter(vault),
        MarkdownIngestionAdapter(vault),
    )

    return IngestionAdapterRegistry(adapters)


class IngestionOrchestrator:
    """Coordinate vault-backed ingestion through registered adapters."""

    def __init__(self, registry: IngestionAdapterRegistry) -> None:
        self._registry = registry

    def ingest(self, request: IngestionRequest) -> IngestionResult:
        adapter = self._registry.get(request.adapter_name)

        if not adapter.can_ingest(request.artifact):
            raise IngestionAdapterError(
                "Registered adapter does not support the requested artifact."
            )

        return adapter.ingest(request)

    def ingest_auto(self, artifact: IngestionArtifactRef) -> IngestionResult:
        adapter = self._registry.resolve(artifact)
        request = IngestionRequest(
            artifact=artifact,
            adapter_name=adapter.adapter_name,
            adapter_version=adapter.adapter_version,
        )

        return adapter.ingest(request)
