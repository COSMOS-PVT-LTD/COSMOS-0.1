"""HTML and Markdown ingestion adapters (NEW KG-012)."""

from __future__ import annotations

from html.parser import HTMLParser

from knowledge.ingestion.models import (
    IngestionRequest,
    IngestionResult,
    NormalizedDocumentFormat,
    SourceFormat,
)
from knowledge.ingestion_adapters.base import VaultBackedAdapter
from knowledge.ingestion_adapters.exceptions import AdapterExecutionError
from knowledge.ingestion_adapters.normalize import build_structured_text_envelope
from knowledge.source.vault import SourceVault

__all__ = (
    "HtmlIngestionAdapter",
    "MarkdownIngestionAdapter",
)


class _StructureHtmlParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.blocks: list[dict[str, str]] = []
        self._current_tag: str | None = None
        self._buffer: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag in {"h1", "h2", "h3", "p", "li", "pre", "code"}:
            self._flush()
            self._current_tag = tag

    def handle_endtag(self, tag: str) -> None:
        if tag == self._current_tag:
            self._flush()

    def handle_data(self, data: str) -> None:
        if self._current_tag is not None and data.strip():
            self._buffer.append(data.strip())

    def _flush(self) -> None:
        if self._current_tag is not None and self._buffer:
            self.blocks.append(
                {
                    "tag": self._current_tag,
                    "text": " ".join(self._buffer),
                },
            )

        self._current_tag = None
        self._buffer = []


class HtmlIngestionAdapter(VaultBackedAdapter):
    """HTML ingestion preserving structural blocks without network access."""

    def __init__(self, vault: SourceVault) -> None:
        super().__init__(
            vault,
            adapter_name="cosmos-html-ingestion",
            adapter_version="0.1.0",
            supported_formats=frozenset({SourceFormat.HTML}),
            parser_version="cosmos-html-ingestion-0.1.0",
        )

    def ingest(self, request: IngestionRequest) -> IngestionResult:
        content = self._load_verified_content(request)
        self._require_format(request.artifact, SourceFormat.HTML)

        try:
            html_text = content.decode("utf-8")
        except UnicodeDecodeError as exc:
            raise AdapterExecutionError(
                "HTML artifact must be UTF-8 encoded."
            ) from exc

        parser = _StructureHtmlParser()
        parser.feed(html_text)
        parser.close()

        envelope = build_structured_text_envelope(
            {
                "blocks": parser.blocks,
                "format": "HTML",
            },
        )

        return self._build_result(
            request,
            envelope,
            normalized_format=NormalizedDocumentFormat.STRUCTURED_TEXT,
        )


class MarkdownIngestionAdapter(VaultBackedAdapter):
    """Markdown ingestion with deterministic line normalization."""

    def __init__(self, vault: SourceVault) -> None:
        super().__init__(
            vault,
            adapter_name="cosmos-markdown-ingestion",
            adapter_version="0.1.0",
            supported_formats=frozenset({SourceFormat.MARKDOWN}),
            parser_version="cosmos-markdown-ingestion-0.1.0",
        )

    def ingest(self, request: IngestionRequest) -> IngestionResult:
        content = self._load_verified_content(request)
        self._require_format(request.artifact, SourceFormat.MARKDOWN)

        try:
            markdown_text = content.decode("utf-8")
        except UnicodeDecodeError as exc:
            raise AdapterExecutionError(
                "Markdown artifact must be UTF-8 encoded."
            ) from exc

        normalized = "\n".join(
            line.rstrip()
            for line in markdown_text.replace("\r\n", "\n").split("\n")
        )

        return self._build_result(
            request,
            normalized,
            normalized_format=NormalizedDocumentFormat.MARKDOWN,
        )
