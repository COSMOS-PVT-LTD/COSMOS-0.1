"""PDF rasterizer backends — provisioned when available, otherwise fail closed."""

from __future__ import annotations

from dataclasses import dataclass
import importlib.util
import io
import re
from typing import Protocol, runtime_checkable

from knowledge.ocr.config import RasterConfiguration, configuration_hash
from knowledge.ocr.images import hash_image
from knowledge.pdf.models import ExtractionStatus

__all__ = (
    "EmbeddedImageRasterizer",
    "PdfRasterizer",
    "PypdfiumRasterizer",
    "RasterizeResult",
    "UnavailableRasterizer",
    "rasterize_page",
    "rasterizer_is_provisioned",
    "select_pdf_rasterizer",
)

_JPEG_STREAM = re.compile(rb"stream\r?\n(\xff\xd8\xff.*?)\r?\nendstream", re.DOTALL)


@dataclass(frozen=True, slots=True, kw_only=True)
class RasterizeResult:
    page_number: int
    dpi: int
    image_format: str
    color_mode: str
    image: bytes
    status: ExtractionStatus
    warning: str | None = None
    source_id: str = ""
    document_id: str = ""
    image_hash: str = ""
    rasterizer: str = ""
    rasterizer_version: str = ""
    configuration_hash: str = ""
    rotation_degrees: int = 0


@runtime_checkable
class PdfRasterizer(Protocol):
    rasterizer_name: str
    rasterizer_version: str

    def available(self) -> bool: ...

    def rasterize_page(
        self,
        content: bytes,
        page_number: int,
        configuration: RasterConfiguration,
        *,
        source_id: str = "",
        document_id: str = "",
    ) -> RasterizeResult: ...


class UnavailableRasterizer:
    rasterizer_name = "cosmos-raster-unavailable"
    rasterizer_version = "1.0.0"

    def available(self) -> bool:
        return False

    def rasterize_page(
        self,
        content: bytes,
        page_number: int,
        configuration: RasterConfiguration | None = None,
        *,
        source_id: str = "",
        document_id: str = "",
    ) -> RasterizeResult:
        del content
        config = configuration or RasterConfiguration()
        return _unavailable(
            page_number,
            config,
            "PDF rasterizer is not provisioned.",
            source_id=source_id,
            document_id=document_id,
            rasterizer=self.rasterizer_name,
            version=self.rasterizer_version,
        )


class PypdfiumRasterizer:
    rasterizer_name = "pypdfium2"
    rasterizer_version = "unknown"

    def available(self) -> bool:
        return importlib.util.find_spec("pypdfium2") is not None

    def rasterize_page(
        self,
        content: bytes,
        page_number: int,
        configuration: RasterConfiguration | None = None,
        *,
        source_id: str = "",
        document_id: str = "",
    ) -> RasterizeResult:
        config = configuration or RasterConfiguration()
        if not self.available():
            return UnavailableRasterizer().rasterize_page(
                content,
                page_number,
                config,
                source_id=source_id,
                document_id=document_id,
            )
        import pypdfium2 as pdfium  # type: ignore[import-untyped]

        version = _pypdfium_version()
        document = None
        try:
            document = pdfium.PdfDocument(content)
            if page_number < 1 or page_number > len(document):
                return _unavailable(
                    page_number,
                    config,
                    f"Page {page_number} is out of range.",
                    source_id=source_id,
                    document_id=document_id,
                    rasterizer=self.rasterizer_name,
                    version=version,
                )
            page = document[page_number - 1]
            scale = max(config.dpi, 1) / 72.0
            bitmap = page.render(scale=scale, rotation=config.rotation_degrees)
            image = bitmap.to_pil()
            if config.color_mode == "gray":
                image = image.convert("L")
            else:
                image = image.convert("RGB")
            buffer = io.BytesIO()
            fmt = "PNG" if config.image_format.lower() == "png" else "JPEG"
            image.save(buffer, format=fmt)
            payload = buffer.getvalue()
        except Exception as exc:
            return _unavailable(
                page_number,
                config,
                f"pypdfium2 rasterization failed: {exc}",
                source_id=source_id,
                document_id=document_id,
                rasterizer=self.rasterizer_name,
                version=version,
            )
        finally:
            if document is not None:
                try:
                    document.close()
                except Exception:
                    pass
        return RasterizeResult(
            page_number=page_number,
            dpi=config.dpi,
            image_format=config.image_format,
            color_mode=config.color_mode,
            image=payload,
            status=ExtractionStatus.TEXT_AVAILABLE,
            warning=None,
            source_id=source_id,
            document_id=document_id,
            image_hash=hash_image(payload),
            rasterizer=self.rasterizer_name,
            rasterizer_version=version,
            configuration_hash=_raster_hash(config),
            rotation_degrees=config.rotation_degrees,
        )


class EmbeddedImageRasterizer:
    rasterizer_name = "cosmos-embedded-image"
    rasterizer_version = "1.0.0"

    def available(self) -> bool:
        return True

    def rasterize_page(
        self,
        content: bytes,
        page_number: int,
        configuration: RasterConfiguration | None = None,
        *,
        source_id: str = "",
        document_id: str = "",
    ) -> RasterizeResult:
        config = configuration or RasterConfiguration()
        jpegs = _JPEG_STREAM.findall(content)
        if page_number < 1 or page_number > len(jpegs):
            return _unavailable(
                page_number,
                config,
                "No embedded page image is recoverable.",
                source_id=source_id,
                document_id=document_id,
                rasterizer=self.rasterizer_name,
                version=self.rasterizer_version,
            )
        payload = jpegs[page_number - 1]
        return RasterizeResult(
            page_number=page_number,
            dpi=config.dpi,
            image_format="jpeg",
            color_mode=config.color_mode,
            image=payload,
            status=ExtractionStatus.TEXT_AVAILABLE,
            warning=None,
            source_id=source_id,
            document_id=document_id,
            image_hash=hash_image(payload),
            rasterizer=self.rasterizer_name,
            rasterizer_version=self.rasterizer_version,
            configuration_hash=_raster_hash(config),
            rotation_degrees=config.rotation_degrees,
        )


def select_pdf_rasterizer() -> PdfRasterizer:
    pypdfium = PypdfiumRasterizer()
    if pypdfium.available():
        return pypdfium
    return EmbeddedImageRasterizer()


def rasterizer_is_provisioned() -> bool:
    return PypdfiumRasterizer().available()


def rasterize_page(
    content: bytes,
    page_number: int,
    *,
    dpi: int = 200,
    image_format: str = "png",
    color_mode: str = "rgb",
    source_id: str = "",
    document_id: str = "",
    rotation_degrees: int = 0,
    rasterizer: PdfRasterizer | None = None,
) -> RasterizeResult:
    """Rasterize one PDF page without mutating the source artifact."""

    config = RasterConfiguration(
        dpi=dpi,
        image_format=image_format,
        color_mode=color_mode,
        rotation_degrees=rotation_degrees,
    )
    backend = rasterizer or select_pdf_rasterizer()
    return backend.rasterize_page(
        content,
        page_number,
        config,
        source_id=source_id,
        document_id=document_id,
    )


def _raster_hash(config: RasterConfiguration) -> str:
    return configuration_hash(
        (
            f"dpi={config.dpi}",
            f"format={config.image_format}",
            f"color={config.color_mode}",
            f"rotation={config.rotation_degrees}",
        ),
    )


def _pypdfium_version() -> str:
    try:
        from importlib.metadata import version

        return version("pypdfium2")
    except Exception:
        return "unknown"


def _unavailable(
    page_number: int,
    config: RasterConfiguration,
    warning: str,
    *,
    source_id: str,
    document_id: str,
    rasterizer: str,
    version: str,
) -> RasterizeResult:
    return RasterizeResult(
        page_number=page_number,
        dpi=config.dpi,
        image_format=config.image_format,
        color_mode=config.color_mode,
        image=b"",
        status=ExtractionStatus.EXTRACTION_UNAVAILABLE,
        warning=warning,
        source_id=source_id,
        document_id=document_id,
        image_hash="",
        rasterizer=rasterizer,
        rasterizer_version=version,
        configuration_hash=_raster_hash(config),
        rotation_degrees=config.rotation_degrees,
    )
