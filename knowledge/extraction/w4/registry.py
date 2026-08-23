"""Extractor registry for KG-BLOCK-007."""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from knowledge.extraction.exceptions import ExtractionValidationError
from knowledge.extraction.w4.exceptions import UnsupportedExtractionError
from knowledge.extraction.w4.models import ExtractionContext, ExtractionResult
from knowledge.extraction.w4.pipeline import W4ExtractionPipeline, extract_document

__all__ = (
    "ExtractionOrchestrator",
    "ExtractionRegistry",
    "StructuredDocumentExtractor",
    "build_default_extraction_registry",
)


@runtime_checkable
class StructuredDocumentExtractor(Protocol):
    """Contract for W4 structured document extractors."""

    @property
    def extractor_name(self) -> str:
        """Return the extractor identifier."""

    @property
    def extractor_version(self) -> str:
        """Return the extractor version string."""

    def extract(self, context: ExtractionContext) -> ExtractionResult:
        """Extract candidates from a parsed document."""


class ExtractionRegistry:
    """Deterministic extractor dispatch registry."""

    def __init__(self, extractors: tuple[StructuredDocumentExtractor, ...]) -> None:
        self._extractors = tuple(extractors)
        self._by_name: dict[str, StructuredDocumentExtractor] = {}

        for extractor in extractors:
            name = extractor.extractor_name

            if name in self._by_name:
                raise ExtractionValidationError(
                    f"Duplicate extractor registration for '{name}'."
                )

            self._by_name[name] = extractor

    def get(self, extractor_name: str) -> StructuredDocumentExtractor:
        try:
            return self._by_name[extractor_name]
        except KeyError as exc:
            raise UnsupportedExtractionError(
                f"No extractor registered with name '{extractor_name}'."
            ) from exc

    def default(self) -> StructuredDocumentExtractor:
        return self._extractors[0]


def build_default_extraction_registry() -> ExtractionRegistry:
    """Build the default BLOCK-007 extraction registry."""

    return ExtractionRegistry((W4ExtractionPipeline(),))


class ExtractionOrchestrator:
    """Coordinate W4 extraction through registered extractors."""

    def __init__(self, registry: ExtractionRegistry) -> None:
        self._registry = registry

    def extract(
        self,
        context: ExtractionContext,
        *,
        extractor_name: str | None = None,
    ) -> ExtractionResult:
        if extractor_name is None:
            return extract_document(context)

        return self._registry.get(extractor_name).extract(context)
