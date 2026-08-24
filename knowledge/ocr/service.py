"""Production OCR service boundary over the existing Tesseract adapter."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from threading import Lock
import uuid

from knowledge.ocr.engine import run_ocr
from knowledge.ocr.health import HealthState, OCRHealth, ocr_health
from knowledge.ocr.models import OCRFailure, OCRResult
from knowledge.ocr.security import MAX_IMAGE_BYTES

__all__ = ("JobStatus", "OCRJob", "OCRService")

_MAX_ATTEMPTS = 2


class JobStatus(Enum):
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    SUCCEEDED = "SUCCEEDED"
    FAILED = "FAILED"
    UNAVAILABLE = "UNAVAILABLE"


@dataclass(frozen=True, slots=True, kw_only=True)
class OCRJob:
    job_id: str
    source_id: str
    document_id: str
    page_number: int
    image_id: str
    status: JobStatus
    attempts: int
    max_attempts: int
    result: OCRResult | None
    error: str | None
    created_at: str
    completed_at: str | None
    backend: str
    backend_version: str
    configuration: tuple[str, ...]


class OCRService:
    """Synchronous, locally executable OCR jobs with retry and audit."""

    def __init__(self, *, max_attempts: int = _MAX_ATTEMPTS) -> None:
        self.max_attempts = max_attempts
        self._lock = Lock()
        self.jobs: list[OCRJob] = []
        self.audit: list[dict[str, str]] = []

    def health(self) -> OCRHealth:
        return ocr_health()

    def extract_page(
        self,
        image: bytes,
        *,
        source_id: str,
        document_id: str,
        page_number: int,
        image_id: str,
    ) -> OCRJob:
        job_id = f"ocr-{uuid.uuid4().hex[:12]}"
        created = datetime.now(timezone.utc).isoformat()
        health = self.health()
        if len(image) > MAX_IMAGE_BYTES:
            job = OCRJob(
                job_id=job_id,
                source_id=source_id,
                document_id=document_id,
                page_number=page_number,
                image_id=image_id,
                status=JobStatus.FAILED,
                attempts=0,
                max_attempts=self.max_attempts,
                result=None,
                error="RESOURCE_LIMIT",
                created_at=created,
                completed_at=created,
                backend=health.backend,
                backend_version=health.version,
                configuration=("limit=image-bytes",),
            )
            self._record(job, "resource-limit")
            return job
        if health.state is HealthState.UNAVAILABLE:
            job = OCRJob(
                job_id=job_id,
                source_id=source_id,
                document_id=document_id,
                page_number=page_number,
                image_id=image_id,
                status=JobStatus.UNAVAILABLE,
                attempts=0,
                max_attempts=self.max_attempts,
                result=None,
                error=health.detail,
                created_at=created,
                completed_at=created,
                backend=health.backend,
                backend_version=health.version,
                configuration=("engine=unavailable",),
            )
            self._record(job, "unavailable")
            return job

        result: OCRResult | None = None
        error: str | None = None
        attempts = 0
        with self._lock:
            while attempts < self.max_attempts:
                attempts += 1
                result = run_ocr(
                    image,
                    source_id=source_id,
                    document_id=document_id,
                    page_number=page_number,
                    image_id=image_id,
                )
                if result.failure is None or result.failure is OCRFailure.LOW_CONFIDENCE:
                    error = None
                    break
                if result.failure is OCRFailure.OCR_UNAVAILABLE:
                    error = result.failure.value
                    break
                error = result.failure.value
                if result.failure is not OCRFailure.OCR_FAILED:
                    break
        status = JobStatus.SUCCEEDED
        if result is None:
            status = JobStatus.FAILED
        elif result.failure is OCRFailure.OCR_UNAVAILABLE:
            status = JobStatus.UNAVAILABLE
        elif result.failure not in {None, OCRFailure.LOW_CONFIDENCE}:
            status = JobStatus.FAILED
        job = OCRJob(
            job_id=job_id,
            source_id=source_id,
            document_id=document_id,
            page_number=page_number,
            image_id=image_id,
            status=status,
            attempts=attempts,
            max_attempts=self.max_attempts,
            result=result,
            error=error,
            created_at=created,
            completed_at=datetime.now(timezone.utc).isoformat(),
            backend=result.adapter_name if result else health.backend,
            backend_version=result.engine_version if result else health.version,
            configuration=result.configuration if result else (),
        )
        self._record(job, status.value.lower())
        return job

    def _record(self, job: OCRJob, event: str) -> None:
        self.jobs.append(job)
        self.audit.append(
            {
                "event": event,
                "job_id": job.job_id,
                "source_id": job.source_id,
                "document_id": job.document_id,
                "status": job.status.value,
            },
        )
