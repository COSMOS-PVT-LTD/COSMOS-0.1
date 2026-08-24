"""Local Tesseract OCR via controlled subprocess. Never invents text."""

from __future__ import annotations

from datetime import datetime, timezone
import os
import shutil
import subprocess
import tempfile

from knowledge.ocr.config import OCRConfiguration
from knowledge.ocr.images import hash_image
from knowledge.ocr.models import BoundingBox, OCRFailure, OCRRegion, OCRResult, RegionType

__all__ = ("TesseractOCRAdapter", "tesseract_is_provisioned", "tesseract_version")

_TESSERACT_BIN = "tesseract"


def tesseract_is_provisioned() -> bool:
    return shutil.which(_TESSERACT_BIN) is not None


def tesseract_version() -> str:
    if not tesseract_is_provisioned():
        return ""
    try:
        output = subprocess.run(
            [_TESSERACT_BIN, "--version"],
            check=False,
            capture_output=True,
            text=True,
            timeout=10,
            shell=False,
        )
    except (OSError, subprocess.TimeoutExpired):
        return ""
    line = (output.stderr or output.stdout).splitlines()
    return line[0].strip() if line else ""


class TesseractOCRAdapter:
    adapter_name = "cosmos-ocr-tesseract"
    adapter_version = "1.1.0"

    def __init__(self, configuration: OCRConfiguration | None = None) -> None:
        self.configuration = configuration or OCRConfiguration()

    def available(self) -> bool:
        return tesseract_is_provisioned()

    def supports(self, image: bytes) -> bool:
        return self.available() and _looks_like_image(image)

    def extract(
        self,
        image: bytes,
        *,
        source_id: str,
        document_id: str,
        page_number: int,
        image_id: str,
    ) -> OCRResult:
        config = self.configuration
        version = tesseract_version()
        stamp = datetime.now(timezone.utc).isoformat()
        cfg = (
            "engine=tesseract",
            f"version={version}",
            f"lang={config.language}",
            f"psm={config.page_segmentation_mode}",
        )
        if not image:
            return _empty(
                source_id,
                document_id,
                page_number,
                image_id,
                OCRFailure.NO_IMAGE,
                stamp,
                cfg,
                version,
                "",
            )
        if not self.available():
            return _empty(
                source_id,
                document_id,
                page_number,
                image_id,
                OCRFailure.OCR_UNAVAILABLE,
                stamp,
                cfg,
                version,
                hash_image(image) if image else "",
            )
        if not _looks_like_image(image):
            return _empty(
                source_id,
                document_id,
                page_number,
                image_id,
                OCRFailure.IMAGE_UNREADABLE,
                stamp,
                cfg,
                version,
                hash_image(image),
            )

        tsv, stderr = _run_tesseract(image, config)
        if tsv is None:
            return _empty(
                source_id,
                document_id,
                page_number,
                image_id,
                OCRFailure.OCR_FAILED,
                stamp,
                cfg + (f"stderr={stderr[:120]}",),
                version,
                hash_image(image),
            )
        regions, tokens, text = _parse_tsv(tsv)
        confidence = sum(tokens) / len(tokens) if tokens else 0.0
        failure: OCRFailure | None = None
        if not text.strip():
            failure = OCRFailure.OCR_FAILED
        elif confidence < config.low_confidence_threshold:
            failure = OCRFailure.LOW_CONFIDENCE
        return OCRResult(
            document_id=document_id,
            source_id=source_id,
            page_number=page_number,
            image_id=image_id,
            text=text,
            confidence=max(0.0, min(confidence / 100.0, 1.0)),
            language=config.language,
            regions=regions,
            processing_method="tesseract-subprocess",
            adapter_name=self.adapter_name,
            adapter_version=self.adapter_version,
            timestamp=stamp,
            failure=failure,
            configuration=cfg,
            image_hash=hash_image(image),
            engine_version=version,
            token_confidences=tuple(tokens),
        )


def _looks_like_image(image: bytes) -> bool:
    return image.startswith(b"\x89PNG") or image.startswith(b"\xff\xd8\xff") or image.startswith(b"BM")


def _run_tesseract(image: bytes, config: OCRConfiguration) -> tuple[str | None, str]:
    suffix = ".png" if image.startswith(b"\x89PNG") else ".jpg"
    handle = tempfile.NamedTemporaryFile(prefix="cosmos-ocr-", suffix=suffix, delete=False)
    try:
        handle.write(image)
        handle.close()
        completed = subprocess.run(
            [
                _TESSERACT_BIN,
                handle.name,
                "stdout",
                "--psm",
                str(config.page_segmentation_mode),
                "-l",
                config.language,
                "tsv",
            ],
            check=False,
            capture_output=True,
            text=True,
            timeout=config.timeout_seconds,
            shell=False,
            cwd=tempfile.gettempdir(),
            env={**os.environ, "OMP_THREAD_LIMIT": "1"},
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        return None, str(exc)
    finally:
        try:
            os.unlink(handle.name)
        except OSError:
            pass
    if completed.returncode != 0 and not completed.stdout.strip():
        return None, completed.stderr.strip()
    return completed.stdout, completed.stderr.strip()


def _parse_tsv(tsv: str) -> tuple[tuple[OCRRegion, ...], list[float], str]:
    regions: list[OCRRegion] = []
    tokens: list[float] = []
    lines: dict[int, list[str]] = {}
    order = 0
    for row in tsv.splitlines()[1:]:
        parts = row.split("\t")
        if len(parts) < 12:
            continue
        try:
            level = int(parts[0])
            line_no = int(parts[4])
            conf = float(parts[10])
        except ValueError:
            continue
        text = parts[11].strip()
        if level != 5 or not text:
            continue
        order += 1
        if conf >= 0:
            tokens.append(conf)
        try:
            box = BoundingBox(
                x=float(parts[6]),
                y=float(parts[7]),
                width=float(parts[8]),
                height=float(parts[9]),
            )
        except ValueError:
            box = None
        regions.append(
            OCRRegion(
                text=text,
                bounding_box=box,
                confidence=max(0.0, min(conf / 100.0, 1.0)) if conf >= 0 else 0.0,
                region_type=_region_type(text),
                reading_order=order,
            ),
        )
        lines.setdefault(line_no, []).append(text)
    reconstructed = "\n".join(" ".join(words) for _, words in sorted(lines.items()))
    return tuple(regions), tokens, reconstructed


def _region_type(text: str) -> RegionType:
    lowered = text.lower()
    if "=" in text:
        return RegionType.EQUATION
    if lowered.startswith("chapter") or lowered[:1].isdigit():
        return RegionType.HEADING
    if lowered.startswith("fig") or lowered.startswith("table"):
        return RegionType.CAPTION
    return RegionType.TEXT


def _empty(
    source_id: str,
    document_id: str,
    page_number: int,
    image_id: str,
    failure: OCRFailure,
    stamp: str,
    configuration: tuple[str, ...],
    version: str,
    image_hash: str,
) -> OCRResult:
    return OCRResult(
        document_id=document_id,
        source_id=source_id,
        page_number=page_number,
        image_id=image_id,
        text="",
        confidence=0.0,
        language="und",
        regions=(),
        processing_method="tesseract-subprocess",
        adapter_name="cosmos-ocr-tesseract",
        adapter_version="1.1.0",
        timestamp=stamp,
        failure=failure,
        configuration=configuration,
        image_hash=image_hash,
        engine_version=version,
        token_confidences=(),
    )
