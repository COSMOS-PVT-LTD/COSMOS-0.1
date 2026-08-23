"""Public exports for knowledge.ingestion_adapters (KG-BLOCK-005 W2)."""

from __future__ import annotations

from knowledge.ingestion_adapters.docx import DocxIngestionAdapter
from knowledge.ingestion_adapters.exceptions import (
    AdapterExecutionError,
    AdapterValidationError,
    RepositoryBoundaryError,
    UnsupportedContentError,
)
from knowledge.ingestion_adapters.html import HtmlIngestionAdapter, MarkdownIngestionAdapter
from knowledge.ingestion_adapters.pdf import PdfIngestionAdapter
from knowledge.ingestion_adapters.pptx import PptxIngestionAdapter
from knowledge.ingestion_adapters.registry import (
    IngestionAdapterRegistry,
    IngestionOrchestrator,
    build_default_registry,
)
from knowledge.ingestion_adapters.repository import (
    RepositoryIngestionAdapter,
    RepositoryIngestionConfig,
    RepositoryIngestionResult,
)
from knowledge.ingestion_adapters.xlsx import XlsxIngestionAdapter

__all__ = (
    "AdapterExecutionError",
    "AdapterValidationError",
    "DocxIngestionAdapter",
    "HtmlIngestionAdapter",
    "IngestionAdapterRegistry",
    "IngestionOrchestrator",
    "MarkdownIngestionAdapter",
    "PdfIngestionAdapter",
    "PptxIngestionAdapter",
    "RepositoryBoundaryError",
    "RepositoryIngestionAdapter",
    "RepositoryIngestionConfig",
    "RepositoryIngestionResult",
    "UnsupportedContentError",
    "XlsxIngestionAdapter",
    "build_default_registry",
)
