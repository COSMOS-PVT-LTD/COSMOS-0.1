"""Backend provisioning probes used by tests and qualification reports."""

from __future__ import annotations

from knowledge.ocr.rasterize import PypdfiumRasterizer
from knowledge.ocr.tesseract import tesseract_is_provisioned, tesseract_version

__all__ = ("ocr_is_provisioned", "provisioning_status", "rasterizer_is_provisioned")


def rasterizer_is_provisioned() -> bool:
    return PypdfiumRasterizer().available()


def ocr_is_provisioned() -> bool:
    return tesseract_is_provisioned()


def provisioning_status() -> dict[str, str | bool]:
    pypdfium = PypdfiumRasterizer()
    return {
        "rasterizer_provisioned": pypdfium.available(),
        "rasterizer_backend": pypdfium.rasterizer_name if pypdfium.available() else "unavailable",
        "ocr_provisioned": tesseract_is_provisioned(),
        "ocr_backend": "tesseract" if tesseract_is_provisioned() else "unavailable",
        "ocr_version": tesseract_version(),
    }
