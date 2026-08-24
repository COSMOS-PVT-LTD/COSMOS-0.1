"""Workspace contracts for intake, jobs, extraction stages, and sources."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

__all__ = (
    "PIPELINE_VERSION",
    "DuplicateKind",
    "ExtractionReport",
    "ExtractionStageReport",
    "IngestionJob",
    "IntakeResult",
    "JobCheckpoint",
    "JobStatus",
    "SourceRecord",
    "StageStatus",
    "WorkspaceFormat",
)

PIPELINE_VERSION = "workspace-1.0.0"


def _as_int(value: object, default: int = 0) -> int:
    if isinstance(value, bool):
        return default
    if isinstance(value, int):
        return value
    if isinstance(value, str) and value.strip().lstrip("-").isdigit():
        return int(value)
    return default


class WorkspaceFormat(Enum):
    """Capability-registry formats. Independent of frozen SourceFormat."""

    PDF = "PDF"
    DOCX = "DOCX"
    PPTX = "PPTX"
    XLSX = "XLSX"
    CSV = "CSV"
    TXT = "TXT"
    MARKDOWN = "MARKDOWN"
    HTML = "HTML"
    LATEX = "LATEX"
    EPUB = "EPUB"
    PNG = "PNG"
    JPEG = "JPEG"
    TIFF = "TIFF"
    WEBP = "WEBP"
    JSON = "JSON"
    XML = "XML"
    UNSUPPORTED = "UNSUPPORTED"


class StageStatus(Enum):
    """Explicit stage outcome. UNAVAILABLE is never treated as EMPTY."""

    SUPPORTED = "SUPPORTED"
    COMPLETED = "COMPLETED"
    PARTIAL = "PARTIAL"
    UNAVAILABLE = "UNAVAILABLE"
    FAILED = "FAILED"
    BLOCKED = "BLOCKED"
    SKIPPED = "SKIPPED"


class JobStatus(Enum):
    RECEIVED = "RECEIVED"
    REGISTERED = "REGISTERED"
    QUEUED = "QUEUED"
    PROCESSING = "PROCESSING"
    EXTRACTING = "EXTRACTING"
    VALIDATING = "VALIDATING"
    REVIEW_REQUIRED = "REVIEW_REQUIRED"
    APPROVED = "APPROVED"
    INDEXING = "INDEXING"
    AVAILABLE = "AVAILABLE"
    FAILED = "FAILED"
    BLOCKED = "BLOCKED"
    CANCELLED = "CANCELLED"


class DuplicateKind(Enum):
    NEW_SOURCE = "NEW_SOURCE"
    EXACT_DUPLICATE = "EXACT_DUPLICATE"
    MODIFIED_SOURCE = "MODIFIED_SOURCE"
    NEW_VERSION = "NEW_VERSION"
    NEW_EDITION = "NEW_EDITION"


@dataclass(frozen=True, slots=True, kw_only=True)
class ExtractionStageReport:
    name: str
    status: StageStatus
    detail: str = ""


@dataclass(frozen=True, slots=True, kw_only=True)
class JobCheckpoint:
    last_completed_page: int | None = None
    last_completed_row: int | None = None
    last_completed_stage: str = ""

    def to_mapping(self) -> dict[str, object]:
        return {
            "last_completed_page": self.last_completed_page,
            "last_completed_row": self.last_completed_row,
            "last_completed_stage": self.last_completed_stage,
        }

    @classmethod
    def from_mapping(cls, payload: dict[str, object] | None) -> JobCheckpoint:
        if not payload:
            return cls()
        page = payload.get("last_completed_page")
        row = payload.get("last_completed_row")
        stage = payload.get("last_completed_stage")
        return cls(
            last_completed_page=_as_int(page) if page is not None else None,
            last_completed_row=_as_int(row) if row is not None else None,
            last_completed_stage=str(stage) if isinstance(stage, str) else "",
        )


@dataclass(frozen=True, slots=True, kw_only=True)
class IngestionJob:
    job_id: str
    source_id: str
    pipeline_version: str
    status: JobStatus
    created_at: str
    started_at: str | None = None
    completed_at: str | None = None
    error_code: str | None = None
    error_message: str | None = None
    attempt: int = 1
    worker: str = "local-sync"
    checkpoint: JobCheckpoint = field(default_factory=JobCheckpoint)
    configuration_hash: str = ""
    source_hash: str = ""

    def to_mapping(self) -> dict[str, object]:
        return {
            "job_id": self.job_id,
            "source_id": self.source_id,
            "pipeline_version": self.pipeline_version,
            "status": self.status.value,
            "created_at": self.created_at,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "error_code": self.error_code,
            "error_message": self.error_message,
            "attempt": self.attempt,
            "worker": self.worker,
            "checkpoint": self.checkpoint.to_mapping(),
            "configuration_hash": self.configuration_hash,
            "source_hash": self.source_hash,
        }

    @classmethod
    def from_mapping(cls, payload: dict[str, object]) -> IngestionJob:
        checkpoint_raw = payload.get("checkpoint")
        checkpoint = JobCheckpoint.from_mapping(
            checkpoint_raw if isinstance(checkpoint_raw, dict) else None,
        )
        return cls(
            job_id=str(payload["job_id"]),
            source_id=str(payload["source_id"]),
            pipeline_version=str(payload["pipeline_version"]),
            status=JobStatus(str(payload["status"])),
            created_at=str(payload["created_at"]),
            started_at=str(payload["started_at"]) if payload.get("started_at") else None,
            completed_at=str(payload["completed_at"]) if payload.get("completed_at") else None,
            error_code=str(payload["error_code"]) if payload.get("error_code") else None,
            error_message=str(payload["error_message"]) if payload.get("error_message") else None,
            attempt=_as_int(payload.get("attempt"), 1),
            worker=str(payload.get("worker") or "local-sync"),
            checkpoint=checkpoint,
            configuration_hash=str(payload.get("configuration_hash") or ""),
            source_hash=str(payload.get("source_hash") or ""),
        )


@dataclass(frozen=True, slots=True, kw_only=True)
class SourceRecord:
    source_id: str
    artifact_id: str
    filename: str
    media_type: str
    extension: str
    size_bytes: int
    sha256: str
    created_at: str
    ingested_at: str
    source_origin: str
    rights_status: str
    license: str | None
    classification: str
    version: int
    parent_source_id: str | None
    storage_uri: str
    integrity_status: str
    workspace_format: str
    project_id: str
    recovered_text: str = ""
    pipeline_version: str = PIPELINE_VERSION
    adapter_version: str = ""
    configuration_hash: str = ""
    title: str = ""
    processing_fingerprint: str = ""

    def to_mapping(self) -> dict[str, object]:
        return {
            "source_id": self.source_id,
            "artifact_id": self.artifact_id,
            "filename": self.filename,
            "media_type": self.media_type,
            "extension": self.extension,
            "size_bytes": self.size_bytes,
            "sha256": self.sha256,
            "created_at": self.created_at,
            "ingested_at": self.ingested_at,
            "source_origin": self.source_origin,
            "rights_status": self.rights_status,
            "license": self.license,
            "classification": self.classification,
            "version": self.version,
            "parent_source_id": self.parent_source_id,
            "storage_uri": self.storage_uri,
            "integrity_status": self.integrity_status,
            "workspace_format": self.workspace_format,
            "project_id": self.project_id,
            "recovered_text": self.recovered_text,
            "pipeline_version": self.pipeline_version,
            "adapter_version": self.adapter_version,
            "configuration_hash": self.configuration_hash,
            "title": self.title,
            "processing_fingerprint": self.processing_fingerprint,
        }

    @classmethod
    def from_mapping(cls, payload: dict[str, object]) -> SourceRecord:
        return cls(
            source_id=str(payload["source_id"]),
            artifact_id=str(payload["artifact_id"]),
            filename=str(payload["filename"]),
            media_type=str(payload["media_type"]),
            extension=str(payload["extension"]),
            size_bytes=_as_int(payload["size_bytes"]),
            sha256=str(payload["sha256"]),
            created_at=str(payload["created_at"]),
            ingested_at=str(payload["ingested_at"]),
            source_origin=str(payload["source_origin"]),
            rights_status=str(payload["rights_status"]),
            license=str(payload["license"]) if payload.get("license") else None,
            classification=str(payload["classification"]),
            version=_as_int(payload["version"], 1),
            parent_source_id=str(payload["parent_source_id"]) if payload.get("parent_source_id") else None,
            storage_uri=str(payload["storage_uri"]),
            integrity_status=str(payload["integrity_status"]),
            workspace_format=str(payload["workspace_format"]),
            project_id=str(payload.get("project_id") or "GLOBAL"),
            recovered_text=str(payload.get("recovered_text") or ""),
            pipeline_version=str(payload.get("pipeline_version") or PIPELINE_VERSION),
            adapter_version=str(payload.get("adapter_version") or ""),
            configuration_hash=str(payload.get("configuration_hash") or ""),
            title=str(payload.get("title") or ""),
            processing_fingerprint=str(payload.get("processing_fingerprint") or ""),
        )


@dataclass(frozen=True, slots=True, kw_only=True)
class ExtractionReport:
    stages: tuple[ExtractionStageReport, ...]
    recovered_text: str = ""
    dataset_id: str | None = None
    equation_candidate_count: int = 0
    adapter_version: str = ""
    warnings: tuple[str, ...] = ()

    def stage(self, name: str) -> ExtractionStageReport | None:
        for item in self.stages:
            if item.name == name:
                return item
        return None


@dataclass(frozen=True, slots=True, kw_only=True)
class IntakeResult:
    job: IngestionJob
    source: SourceRecord | None
    extraction: ExtractionReport | None
    duplicate_kind: DuplicateKind
    idempotent_replay: bool = False
