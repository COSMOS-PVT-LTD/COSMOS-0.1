"""Ingestion job state machine, checkpoints, and idempotent fingerprints."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
import json

from knowledge.source.integrity import sha256_text_digest
from knowledge.workspace.models import IngestionJob, JobCheckpoint, JobStatus, PIPELINE_VERSION

__all__ = (
    "JobStore",
    "configuration_hash",
    "now_utc",
    "processing_fingerprint",
)


def now_utc() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def configuration_hash(
    *,
    pipeline_version: str,
    rights_status: str,
    ocr_enabled: bool,
) -> str:
    payload = json.dumps(
        {
            "ocr_enabled": ocr_enabled,
            "pipeline_version": pipeline_version,
            "rights_status": rights_status,
        },
        sort_keys=True,
        separators=(",", ":"),
    )
    return sha256_text_digest(payload)


def processing_fingerprint(source_hash: str, pipeline_version: str, config_hash: str) -> str:
    return sha256_text_digest(f"{source_hash}:{pipeline_version}:{config_hash}")


class JobStore:
    def __init__(self, root: Path | str | None = None) -> None:
        self.root = Path(root) if root is not None else None
        self._jobs: dict[str, IngestionJob] = {}
        if self.root is not None:
            self.root.mkdir(parents=True, exist_ok=True)
            self._load()

    def create(
        self,
        *,
        source_id: str,
        source_hash: str,
        pipeline_version: str = PIPELINE_VERSION,
        configuration_hash_value: str,
        worker: str = "local-sync",
    ) -> IngestionJob:
        fingerprint = processing_fingerprint(source_hash, pipeline_version, configuration_hash_value)
        job_id = f"JOB-{fingerprint[:16]}"
        job = IngestionJob(
            job_id=job_id,
            source_id=source_id,
            pipeline_version=pipeline_version,
            status=JobStatus.RECEIVED,
            created_at=now_utc(),
            configuration_hash=configuration_hash_value,
            source_hash=source_hash,
            worker=worker,
        )
        return self.save(job)

    def save(self, job: IngestionJob) -> IngestionJob:
        self._jobs[job.job_id] = job
        if self.root is not None:
            path = self.root / f"{job.job_id}.json"
            path.write_text(json.dumps(job.to_mapping(), indent=2, sort_keys=True), encoding="utf-8")
        return job

    def get(self, job_id: str) -> IngestionJob:
        return self._jobs[job_id]

    def find_by_fingerprint(self, fingerprint: str) -> IngestionJob | None:
        job_id = f"JOB-{fingerprint[:16]}"
        return self._jobs.get(job_id)

    def list_jobs(self) -> tuple[IngestionJob, ...]:
        return tuple(sorted(self._jobs.values(), key=lambda item: item.created_at))

    def find_latest_for_source(self, source_id: str) -> IngestionJob | None:
        matches = [job for job in self._jobs.values() if job.source_id == source_id]
        if not matches:
            return None
        return max(matches, key=lambda item: item.created_at)

    def prune_for_source(self, source_id: str, *, keep_job_id: str) -> int:
        removed = 0
        doomed = [
            job_id
            for job_id, job in self._jobs.items()
            if job.source_id == source_id and job.job_id != keep_job_id
        ]
        for job_id in doomed:
            self._jobs.pop(job_id, None)
            removed += 1
            if self.root is not None:
                path = self.root / f"{job_id}.json"
                if path.is_file():
                    path.unlink()
        return removed

    def delete_for_source(self, source_id: str) -> None:
        doomed = [job_id for job_id, job in self._jobs.items() if job.source_id == source_id]
        for job_id in doomed:
            self._jobs.pop(job_id, None)
            if self.root is not None:
                path = self.root / f"{job_id}.json"
                if path.is_file():
                    path.unlink()

    def transition(
        self,
        job: IngestionJob,
        status: JobStatus,
        *,
        error_code: str | None = None,
        error_message: str | None = None,
        checkpoint: JobCheckpoint | None = None,
        increment_attempt: bool = False,
    ) -> IngestionJob:
        started = job.started_at
        completed = job.completed_at
        stamp = now_utc()
        if status is JobStatus.PROCESSING and started is None:
            started = stamp
        if status in {JobStatus.AVAILABLE, JobStatus.FAILED, JobStatus.BLOCKED, JobStatus.CANCELLED, JobStatus.APPROVED}:
            completed = stamp
        updated = IngestionJob(
            job_id=job.job_id,
            source_id=job.source_id,
            pipeline_version=job.pipeline_version,
            status=status,
            created_at=job.created_at,
            started_at=started,
            completed_at=completed,
            error_code=error_code,
            error_message=error_message,
            attempt=job.attempt + 1 if increment_attempt else job.attempt,
            worker=job.worker,
            checkpoint=checkpoint or job.checkpoint,
            configuration_hash=job.configuration_hash,
            source_hash=job.source_hash,
        )
        return self.save(updated)

    def _load(self) -> None:
        if self.root is None:
            return
        for path in sorted(self.root.glob("JOB-*.json")):
            payload = json.loads(path.read_text(encoding="utf-8"))
            job = IngestionJob.from_mapping(payload)
            self._jobs[job.job_id] = job
