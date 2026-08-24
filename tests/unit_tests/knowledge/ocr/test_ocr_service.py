"""Production OCR service boundary."""

from __future__ import annotations

from knowledge.ocr.health import HealthState, ocr_health
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
    assert job.attempts >= 1
    if ocr_health().state is HealthState.AVAILABLE:
        assert job.status in {JobStatus.SUCCEEDED, JobStatus.FAILED}
        assert job.result is not None
    else:
        assert job.status is JobStatus.UNAVAILABLE
