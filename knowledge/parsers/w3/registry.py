"""Parser registry and orchestration for KG-BLOCK-006."""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from knowledge.parsers.w3.content import ParseContext, ParseResult
from knowledge.parsers.w3.exceptions import ParserStructureError
from knowledge.parsers.w3.pipeline import W3DocumentParser, parse_document

__all__ = (
    "ParserOrchestrator",
    "ParserRegistry",
    "StructuredDocumentParser",
    "build_default_parser_registry",
)


@runtime_checkable
class StructuredDocumentParser(Protocol):
    """Contract for W3 structured document parsers."""

    @property
    def parser_name(self) -> str:
        """Return the parser identifier."""

    @property
    def parser_version(self) -> str:
        """Return the parser version string."""

    def parse(self, context: ParseContext) -> ParseResult:
        """Parse normalized ingestion content."""


class ParserRegistry:
    """Deterministic parser dispatch registry."""

    def __init__(self, parsers: tuple[StructuredDocumentParser, ...]) -> None:
        self._parsers = tuple(parsers)
        self._by_name = {parser.parser_name: parser for parser in parsers}

    def get(self, parser_name: str) -> StructuredDocumentParser:
        try:
            return self._by_name[parser_name]
        except KeyError as exc:
            raise ParserStructureError(
                f"No parser registered with name '{parser_name}'."
            ) from exc

    def default(self) -> StructuredDocumentParser:
        return self._parsers[0]

    def parsers(self) -> tuple[StructuredDocumentParser, ...]:
        return self._parsers


def build_default_parser_registry() -> ParserRegistry:
    """Build the default BLOCK-006 parser registry."""

    return ParserRegistry((W3DocumentParser(),))


class ParserOrchestrator:
    """Coordinate W3 parsing through registered parsers."""

    def __init__(self, registry: ParserRegistry) -> None:
        self._registry = registry

    def parse(self, context: ParseContext, *, parser_name: str | None = None) -> ParseResult:
        if parser_name is None:
            return parse_document(context)

        parser = self._registry.get(parser_name)

        return parser.parse(context)
