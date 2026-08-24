"""Supported file capability registry. Unsupported types fail closed."""

from __future__ import annotations

from dataclasses import dataclass

from knowledge.workspace.models import StageStatus, WorkspaceFormat

__all__ = (
    "FileCapability",
    "FileCapabilityRegistry",
    "default_capability_registry",
)


@dataclass(frozen=True, slots=True, kw_only=True)
class FileCapability:
    workspace_format: WorkspaceFormat
    extensions: tuple[str, ...]
    media_types: tuple[str, ...]
    text: StageStatus
    tables: StageStatus
    images: StageStatus
    ocr: StageStatus
    math_ocr: StageStatus
    datasets: StageStatus
    notes: str


class FileCapabilityRegistry:
    def __init__(self, capabilities: tuple[FileCapability, ...]) -> None:
        self._capabilities = capabilities
        self._by_format = {item.workspace_format: item for item in capabilities}
        self._by_extension: dict[str, FileCapability] = {}
        for item in capabilities:
            for extension in item.extensions:
                self._by_extension[extension.lower()] = item

    def get(self, workspace_format: WorkspaceFormat) -> FileCapability | None:
        return self._by_format.get(workspace_format)

    def by_extension(self, extension: str) -> FileCapability | None:
        cleaned = extension.lower().lstrip(".")
        if not cleaned:
            return None
        return self._by_extension.get(f".{cleaned}" if not cleaned.startswith(".") else cleaned) or self._by_extension.get(f".{cleaned}")

    def is_supported(self, workspace_format: WorkspaceFormat) -> bool:
        return workspace_format is not WorkspaceFormat.UNSUPPORTED and workspace_format in self._by_format

    def all(self) -> tuple[FileCapability, ...]:
        return self._capabilities


def default_capability_registry() -> FileCapabilityRegistry:
    available = StageStatus.SUPPORTED
    unavailable = StageStatus.UNAVAILABLE
    capabilities = (
        FileCapability(
            workspace_format=WorkspaceFormat.PDF,
            extensions=(".pdf",),
            media_types=("application/pdf",),
            text=available,
            tables=available,
            images=available,
            ocr=available,
            math_ocr=available,
            datasets=unavailable,
            notes="Native text + provisioned OCR. Math-OCR is the Tesseract equation-span adapter, not a dedicated engine.",
        ),
        FileCapability(
            workspace_format=WorkspaceFormat.DOCX,
            extensions=(".docx",),
            media_types=("application/vnd.openxmlformats-officedocument.wordprocessingml.document",),
            text=available,
            tables=StageStatus.PARTIAL,
            images=unavailable,
            ocr=unavailable,
            math_ocr=unavailable,
            datasets=unavailable,
            notes="Paragraph extraction via frozen DOCX adapter contracts.",
        ),
        FileCapability(
            workspace_format=WorkspaceFormat.PPTX,
            extensions=(".pptx",),
            media_types=("application/vnd.openxmlformats-officedocument.presentationml.presentation",),
            text=available,
            tables=unavailable,
            images=unavailable,
            ocr=unavailable,
            math_ocr=unavailable,
            datasets=unavailable,
            notes="Slide text extraction.",
        ),
        FileCapability(
            workspace_format=WorkspaceFormat.XLSX,
            extensions=(".xlsx",),
            media_types=("application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",),
            text=StageStatus.PARTIAL,
            tables=available,
            images=unavailable,
            ocr=unavailable,
            math_ocr=unavailable,
            datasets=available,
            notes="Cell values only. Formulas are not executed.",
        ),
        FileCapability(
            workspace_format=WorkspaceFormat.CSV,
            extensions=(".csv",),
            media_types=("text/csv", "application/csv"),
            text=StageStatus.PARTIAL,
            tables=available,
            images=unavailable,
            ocr=unavailable,
            math_ocr=unavailable,
            datasets=available,
            notes="Schema + rows. Units only when declared in the header.",
        ),
        FileCapability(
            workspace_format=WorkspaceFormat.TXT,
            extensions=(".txt",),
            media_types=("text/plain",),
            text=available,
            tables=unavailable,
            images=unavailable,
            ocr=unavailable,
            math_ocr=unavailable,
            datasets=unavailable,
            notes="UTF-8 text.",
        ),
        FileCapability(
            workspace_format=WorkspaceFormat.MARKDOWN,
            extensions=(".md", ".markdown"),
            media_types=("text/markdown",),
            text=available,
            tables=StageStatus.PARTIAL,
            images=unavailable,
            ocr=unavailable,
            math_ocr=unavailable,
            datasets=unavailable,
            notes="Markdown ingest to candidate extraction.",
        ),
        FileCapability(
            workspace_format=WorkspaceFormat.HTML,
            extensions=(".html", ".htm"),
            media_types=("text/html",),
            text=available,
            tables=StageStatus.PARTIAL,
            images=unavailable,
            ocr=unavailable,
            math_ocr=unavailable,
            datasets=unavailable,
            notes="Structure-preserving HTML blocks.",
        ),
        FileCapability(
            workspace_format=WorkspaceFormat.LATEX,
            extensions=(".tex", ".latex"),
            media_types=("application/x-tex", "text/x-tex"),
            text=available,
            tables=unavailable,
            images=unavailable,
            ocr=unavailable,
            math_ocr=StageStatus.PARTIAL,
            datasets=unavailable,
            notes="Ingested as source-faithful text. Not a TeX compiler.",
        ),
        FileCapability(
            workspace_format=WorkspaceFormat.EPUB,
            extensions=(".epub",),
            media_types=("application/epub+zip",),
            text=available,
            tables=unavailable,
            images=unavailable,
            ocr=unavailable,
            math_ocr=unavailable,
            datasets=unavailable,
            notes="ZIP HTML/XHTML extraction when present.",
        ),
        FileCapability(
            workspace_format=WorkspaceFormat.PNG,
            extensions=(".png",),
            media_types=("image/png",),
            text=unavailable,
            tables=unavailable,
            images=available,
            ocr=available,
            math_ocr=unavailable,
            datasets=unavailable,
            notes="OCR when Tesseract is provisioned; otherwise EXTRACTION_UNAVAILABLE.",
        ),
        FileCapability(
            workspace_format=WorkspaceFormat.JPEG,
            extensions=(".jpg", ".jpeg"),
            media_types=("image/jpeg",),
            text=unavailable,
            tables=unavailable,
            images=available,
            ocr=available,
            math_ocr=unavailable,
            datasets=unavailable,
            notes="OCR when Tesseract is provisioned.",
        ),
        FileCapability(
            workspace_format=WorkspaceFormat.TIFF,
            extensions=(".tif", ".tiff"),
            media_types=("image/tiff",),
            text=unavailable,
            tables=unavailable,
            images=available,
            ocr=available,
            math_ocr=unavailable,
            datasets=unavailable,
            notes="OCR when Tesseract is provisioned.",
        ),
        FileCapability(
            workspace_format=WorkspaceFormat.WEBP,
            extensions=(".webp",),
            media_types=("image/webp",),
            text=unavailable,
            tables=unavailable,
            images=available,
            ocr=StageStatus.PARTIAL,
            math_ocr=unavailable,
            datasets=unavailable,
            notes="Registered as an image original. OCR depends on engine image support.",
        ),
        FileCapability(
            workspace_format=WorkspaceFormat.JSON,
            extensions=(".json",),
            media_types=("application/json",),
            text=StageStatus.PARTIAL,
            tables=StageStatus.PARTIAL,
            images=unavailable,
            ocr=unavailable,
            math_ocr=unavailable,
            datasets=available,
            notes="List-of-objects becomes a dataset. Other JSON is structured extraction.",
        ),
        FileCapability(
            workspace_format=WorkspaceFormat.XML,
            extensions=(".xml",),
            media_types=("application/xml", "text/xml"),
            text=available,
            tables=unavailable,
            images=unavailable,
            ocr=unavailable,
            math_ocr=unavailable,
            datasets=StageStatus.PARTIAL,
            notes="Element text extraction. Not a generic XML-to-dataset mapper.",
        ),
    )
    return FileCapabilityRegistry(capabilities)
