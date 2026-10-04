"""Production OCR service boundary."""

from __future__ import annotations

from unittest.mock import patch

from knowledge.ocr.health import HealthState, OCRHealth, ocr_health
from knowledge.ocr.security import MAX_IMAGE_BYTES
from knowledge.ocr.service import JobStatus, OCRService
from knowledge.pdf.image_pdf import render_text_page_image


def test_health_distinguishes_available_and_unavailable() -> None:
    health = ocr_health()
    assert health.state in {
        HealthState.AVAILABLE,
        HealthState.UNAVAILABLE,
        HealthState.MISCONFIGURED,
        HealthState.FAILED,
    }


def test_resource_limit_fails_closed() -> None:
    service = OCRService()
    job = service.extract_page(
        b"x" * (MAX_IMAGE_BYTES + 1),
        source_id="SRC",
        document_id="DOC",
        page_number=1,
        image_id="big",
    )
    assert job.status is JobStatus.FAILED
    assert job.error == "RESOURCE_LIMIT"
    assert job.result is None
    assert service.audit


def test_job_records_backend_when_image_is_valid() -> None:
    service = OCRService()
    image = render_text_page_image(("Eq. 1 Re = rho * V * D / mu",))
    job = service.extract_page(
        image,
        source_id="SRC",
        document_id="DOC",
        page_number=1,
        image_id="img",
    )
    assert job.job_id
    if ocr_health().state is HealthState.UNAVAILABLE:
        assert job.status is JobStatus.UNAVAILABLE
        assert job.attempts == 0
        assert job.result is None
        assert job.configuration == ("engine=unavailable",)
    else:
        assert job.attempts >= 1
        assert job.status in {JobStatus.SUCCEEDED, JobStatus.FAILED}
        assert job.result is not None


def test_missing_ocr_backend_records_unavailable_without_attempting_extraction() -> None:
    service = OCRService()
    image = render_text_page_image(("Eq. 1 Re = rho * V * D / mu",))
    health = OCRHealth(
        state=HealthState.UNAVAILABLE,
        backend="tesseract",
        version="",
        detail="tesseract binary not found",
    )
    with (
        patch("knowledge.ocr.service.ocr_health", return_value=health),
        patch("knowledge.ocr.service.run_ocr") as engine,
    ):
        job = service.extract_page(
            image,
            source_id="SRC",
            document_id="DOC",
            page_number=1,
            image_id="img",
        )
    engine.assert_not_called()
    assert job.status is JobStatus.UNAVAILABLE
    assert job.attempts == 0
    assert job.result is None
    assert job.error == health.detail
    assert job.configuration == ("engine=unavailable",)
    assert service.jobs == [job]
    assert service.audit[0]["event"] == "unavailable"
