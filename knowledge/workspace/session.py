"""Authoritative Knowledge Workspace session: intake, vault, jobs, search, review."""

from __future__ import annotations

from dataclasses import dataclass, replace
from pathlib import Path
import json

from knowledge.foundation.document_pipeline import DocumentKnowledgeDraft
from knowledge.foundation.equation_approval import EquationReviewDecision, NormalizedEquationCandidate
from knowledge.foundation.knowledge_service import KnowledgeFoundationService
from knowledge.foundation.real_document_pipeline import RealDocumentPipelineResult
from knowledge.foundation.unified_search import UnifiedSearchResult
from knowledge.models.lifecycle import KnowledgeLifecycle
from knowledge.ocr.provisioning import ocr_is_provisioned
from knowledge.persistence.backend import InMemoryPersistenceBackend, PersistenceBackend, SQLitePersistenceBackend
from knowledge.references.rights import RightsStatus, rights_allow_ingestion
from knowledge.source.integrity import sha256_bytes_digest
from knowledge.workspace.access import WorkspaceAction, WorkspaceAuthorization, WorkspaceRole
from knowledge.workspace.backup import backup_workspace_root, restore_workspace_root
from knowledge.workspace.capabilities import FileCapabilityRegistry, default_capability_registry
from knowledge.workspace.classify import classify_upload
from knowledge.workspace.extract import extract_upload
from knowledge.workspace.jobs import JobStore, configuration_hash, now_utc, processing_fingerprint
from knowledge.workspace.models import (
    PIPELINE_VERSION,
    DuplicateKind,
    ExtractionReport,
    ExtractionStageReport,
    IngestionJob,
    IntakeResult,
    JobCheckpoint,
    JobStatus,
    SourceRecord,
    StageStatus,
    WorkspaceFormat,
)
from knowledge.workspace.observability import WorkspaceMetrics
from knowledge.workspace.security import validate_upload
from knowledge.workspace.vault import DurableArtifactVault, VaultError
from knowledge.workspace.quality import pdf_extraction_is_under_recovered

__all__ = (
    "DocumentEvidenceHit",
    "DocumentEvidenceIndex",
    "KnowledgeWorkspace",
    "ReviewItem",
    "ingest",
)


@dataclass(frozen=True, slots=True, kw_only=True)
class DocumentEvidenceHit:
    source_id: str
    title: str
    snippet: str
    project_id: str
    score: float
    lifecycle: str = KnowledgeLifecycle.EXTRACTED.value
    validation_state: str = "CANDIDATE"


@dataclass(frozen=True, slots=True, kw_only=True)
class ReviewItem:
    source_id: str
    candidate_id: str
    title: str
    expression: str
    validation_state: str


class DocumentEvidenceIndex:
    def __init__(self) -> None:
        self._records: dict[str, SourceRecord] = {}

    def add(self, record: SourceRecord) -> None:
        if record.recovered_text.strip():
            self._records[record.source_id] = record

    def remove(self, source_id: str) -> None:
        self._records.pop(source_id, None)

    def search(self, query: str, *, project_id: str | None = None) -> tuple[DocumentEvidenceHit, ...]:
        tokens = tuple(token for token in query.lower().split() if token)
        if not tokens:
            return ()
        hits: list[DocumentEvidenceHit] = []
        for record in self._records.values():
            if project_id and project_id != "GLOBAL" and record.project_id not in {project_id, "GLOBAL"}:
                continue
            haystack = f"{record.title} {record.filename} {record.recovered_text}".lower()
            matched = sum(1 for token in tokens if token in haystack)
            if matched == 0:
                continue
            snippet = _snippet(record.recovered_text, tokens[0])
            hits.append(
                DocumentEvidenceHit(
                    source_id=record.source_id,
                    title=record.title or record.filename,
                    snippet=snippet,
                    project_id=record.project_id,
                    score=matched / len(tokens),
                ),
            )
        return tuple(sorted(hits, key=lambda item: (-item.score, item.source_id)))

    def rebuild(self, records: tuple[SourceRecord, ...]) -> int:
        self._records.clear()
        for record in records:
            self.add(record)
        return len(self._records)


class KnowledgeWorkspace:
    """Local knowledge workspace bound to one root directory or an in-memory vault."""

    def __init__(
        self,
        root: Path | str | None = None,
        *,
        service: KnowledgeFoundationService | None = None,
        seed_corpus: bool = False,
        project_id: str = "GLOBAL",
        role: WorkspaceRole = WorkspaceRole.ADMIN,
        actor_id: str = "workspace-user",
        pipeline_version: str = PIPELINE_VERSION,
    ) -> None:
        self.root = Path(root) if root is not None else None
        if self.root is not None:
            self.root.mkdir(parents=True, exist_ok=True)
            self.vault = DurableArtifactVault(self.root / "knowledge_vault")
            self.jobs = JobStore(self.root / "jobs")
            self.persistence: PersistenceBackend = SQLitePersistenceBackend(self.root / "workspace.sqlite")
            self.persistence.migrate()
        else:
            self.vault = DurableArtifactVault()
            self.jobs = JobStore()
            self.persistence = InMemoryPersistenceBackend()
            self.persistence.migrate()
        self._service = service
        self._seed_corpus_loaded = False
        if service is not None and seed_corpus:
            self._ensure_seed_corpus()
        self.project_id = project_id
        self.role = role
        self.actor_id = actor_id
        self.pipeline_version = pipeline_version
        self.registry: FileCapabilityRegistry = default_capability_registry()
        self.authz = WorkspaceAuthorization()
        self.metrics = WorkspaceMetrics()
        self.documents = DocumentEvidenceIndex()
        self.datasets: dict[str, dict[str, object]] = {}
        self._pipeline_results: dict[str, RealDocumentPipelineResult] = {}
        self._drafts: dict[str, DocumentKnowledgeDraft] = {}
        self._conversations: object | None = None
        self.documents.rebuild(self.vault.list_sources())
        self._backfill_review_manifests()

    def _backfill_review_manifests(self) -> None:
        from knowledge.workspace.review_store import load_review_manifest, save_review_manifest

        for job in self.list_jobs():
            if job.status is not JobStatus.REVIEW_REQUIRED:
                continue
            if load_review_manifest(self.vault, job.source_id) is not None:
                continue
            source = self.vault.get(job.source_id)
            preview = (source.recovered_text or source.title or source.filename)[:160]
            save_review_manifest(
                self.vault,
                source_id=job.source_id,
                equation_candidate_count=1,
                sample_expressions=(preview or "Document pending approval",),
            )

    @property
    def service(self) -> KnowledgeFoundationService:
        if self._service is None:
            self._service = KnowledgeFoundationService()
        return self._service

    def _ensure_seed_corpus(self) -> None:
        if self._seed_corpus_loaded:
            return
        if self._service is None:
            self._service = KnowledgeFoundationService.with_seed_corpus()
        elif not self._service.physical_laws.query():
            from knowledge.foundation.seed_corpus import populate_seed_corpus

            populate_seed_corpus(self._service)
        self._seed_corpus_loaded = True

    @property
    def conversations(self):  # noqa: ANN201
        from knowledge.brain.chat import KnowledgeConversationService

        if self._conversations is None:
            self._conversations = KnowledgeConversationService(self)
        return self._conversations

    def ingest(
        self,
        file: bytes,
        *,
        filename: str,
        rights_status: RightsStatus = RightsStatus.INTERNAL,
        project_id: str | None = None,
        parent_source_id: str | None = None,
        title: str | None = None,
        pipeline_version: str | None = None,
        reprocess: bool = False,
        edition: str | None = None,
    ) -> IntakeResult:
        self.authz.authorize(self.role, WorkspaceAction.INGEST, actor_id=self.actor_id)
        security = validate_upload(file, filename)
        pipeline = pipeline_version or self.pipeline_version
        if not security.accepted:
            job = self.jobs.create(
                source_id="SRC-REJECTED",
                source_hash=sha256_bytes_digest(file) if isinstance(file, bytes) and file else "0" * 64,
                pipeline_version=pipeline,
                configuration_hash_value=configuration_hash(
                    pipeline_version=pipeline,
                    rights_status=rights_status.value,
                    ocr_enabled=ocr_is_provisioned(),
                ),
            )
            job = self.jobs.transition(
                job,
                JobStatus.FAILED,
                error_code=security.error_code,
                error_message=security.reason,
            )
            self.metrics.ingest_failed += 1
            return IntakeResult(job=job, source=None, extraction=None, duplicate_kind=DuplicateKind.NEW_SOURCE)

        classification = classify_upload(file, security.safe_filename, registry=self.registry)
        digest = sha256_bytes_digest(file)
        config = configuration_hash(
            pipeline_version=pipeline,
            rights_status=rights_status.value,
            ocr_enabled=ocr_is_provisioned(),
        )
        fingerprint = processing_fingerprint(digest, pipeline, config)
        existing_job = self.jobs.find_by_fingerprint(fingerprint)
        success_states = {JobStatus.AVAILABLE, JobStatus.REVIEW_REQUIRED, JobStatus.BLOCKED}
        if existing_job is not None and existing_job.status in success_states and not reprocess:
            source = None
            try:
                source = self.vault.get(existing_job.source_id)
            except VaultError:
                source = None
            if source is not None and pdf_extraction_is_under_recovered(source, existing_job):
                content = self.vault.retrieve_original(source.source_id)
                return self.ingest(
                    content,
                    filename=source.filename,
                    rights_status=RightsStatus(source.rights_status),
                    project_id=source.project_id,
                    title=source.title,
                    pipeline_version=pipeline,
                    reprocess=True,
                )
            self.metrics.ingest_duplicates += 1
            return IntakeResult(
                job=existing_job,
                source=source,
                extraction=None,
                duplicate_kind=DuplicateKind.EXACT_DUPLICATE,
                idempotent_replay=True,
            )

        duplicate_kind, version, parent = self._identity(
            digest,
            security.safe_filename,
            parent_source_id=parent_source_id,
            edition=edition,
        )
        source_id = f"SRC-{digest[:16]}"
        if duplicate_kind is DuplicateKind.MODIFIED_SOURCE:
            source_id = f"SRC-{digest[:16]}"
        if reprocess:
            prior_job = self.jobs.find_latest_for_source(source_id)
            if prior_job is not None:
                existing_job = prior_job
        artifact_id = f"ART-{digest[16:32]}"
        document_id = f"DOC-{digest[:16]}"
        stamp = now_utc()
        record = SourceRecord(
            source_id=source_id,
            artifact_id=artifact_id,
            filename=security.safe_filename,
            media_type=classification.media_type,
            extension=classification.extension,
            size_bytes=len(file),
            sha256=digest,
            created_at=stamp,
            ingested_at=stamp,
            source_origin="workspace-upload",
            rights_status=rights_status.value,
            license=None,
            classification=classification.workspace_format.value,
            version=version,
            parent_source_id=parent,
            storage_uri="",
            integrity_status="PENDING",
            workspace_format=classification.workspace_format.value,
            project_id=project_id or self.project_id,
            pipeline_version=pipeline,
            configuration_hash=config,
            title=title or security.safe_filename,
            processing_fingerprint=fingerprint,
        )
        stored = self.vault.store_original(record, file)
        job = existing_job or self.jobs.create(
            source_id=source_id,
            source_hash=digest,
            pipeline_version=pipeline,
            configuration_hash_value=config,
        )
        if existing_job is not None and reprocess:
            job = IngestionJob(
                job_id=existing_job.job_id,
                source_id=source_id,
                pipeline_version=pipeline,
                status=JobStatus.QUEUED,
                created_at=existing_job.created_at,
                started_at=None,
                completed_at=None,
                error_code=None,
                error_message=None,
                attempt=existing_job.attempt + 1,
                worker=existing_job.worker,
                checkpoint=JobCheckpoint(),
                configuration_hash=config,
                source_hash=digest,
            )
            job = self.jobs.save(job)
        job = self.jobs.transition(job, JobStatus.REGISTERED, checkpoint=JobCheckpoint(last_completed_stage="REGISTERED"))
        job = self.jobs.transition(job, JobStatus.QUEUED)
        job = self.jobs.transition(job, JobStatus.PROCESSING)

        if classification.workspace_format is WorkspaceFormat.UNSUPPORTED:
            job = self.jobs.transition(
                job,
                JobStatus.FAILED,
                error_code="UNSUPPORTED_FORMAT",
                error_message=classification.reason,
            )
            self.metrics.ingest_failed += 1
            return IntakeResult(job=job, source=stored, extraction=None, duplicate_kind=duplicate_kind)

        if not rights_allow_ingestion(rights_status):
            blocked = ExtractionReport(
                stages=(
                    ExtractionStageReport(name="rights", status=StageStatus.BLOCKED, detail=rights_status.value),
                    ExtractionStageReport(name="text", status=StageStatus.BLOCKED, detail="RIGHTS_BLOCKED"),
                ),
                warnings=("RIGHTS_BLOCKED",),
            )
            job = self.jobs.transition(
                job,
                JobStatus.BLOCKED,
                error_code="RIGHTS_BLOCKED",
                error_message=f"Rights status {rights_status.value} is not ingestible.",
                checkpoint=JobCheckpoint(last_completed_stage="RIGHTS_BLOCKED"),
            )
            self.metrics.ingest_blocked += 1
            self.persistence.put("sources", stored.source_id, stored.to_mapping())
            return IntakeResult(job=job, source=stored, extraction=blocked, duplicate_kind=duplicate_kind)

        job = self.jobs.transition(job, JobStatus.EXTRACTING, checkpoint=JobCheckpoint(last_completed_stage="EXTRACTING"))
        try:
            extracted = extract_upload(
                file,
                classification,
                source_id=source_id,
                document_id=document_id,
                title=stored.title,
                filename=stored.filename,
                reference_id=f"REF-{digest[:16]}",
                service=self.service,
                checkpoint=job.checkpoint,
            )
        except (UnicodeDecodeError, ValueError, json.JSONDecodeError) as exc:
            job = self.jobs.transition(
                job,
                JobStatus.FAILED,
                error_code="EXTRACTION_FAILED",
                error_message=str(exc),
            )
            self.metrics.ingest_failed += 1
            return IntakeResult(job=job, source=stored, extraction=None, duplicate_kind=duplicate_kind)

        report = extracted.report
        failed = any(stage.status is StageStatus.FAILED for stage in report.stages)
        unavailable_only = any(stage.status is StageStatus.UNAVAILABLE for stage in report.stages) and not report.recovered_text
        if failed and not report.recovered_text:
            job = self.jobs.transition(
                job,
                JobStatus.FAILED,
                error_code="EXTRACTION_FAILED",
                error_message="; ".join(report.warnings) or "extraction failed",
                checkpoint=extracted.checkpoint,
            )
            self.metrics.ingest_failed += 1
            return IntakeResult(job=job, source=stored, extraction=report, duplicate_kind=duplicate_kind)
        if unavailable_only:
            job = self.jobs.transition(
                job,
                JobStatus.FAILED,
                error_code="EXTRACTION_UNAVAILABLE",
                error_message="; ".join(report.warnings) or "No recoverable text from document.",
                checkpoint=extracted.checkpoint,
            )
            self.metrics.ingest_failed += 1
            return IntakeResult(job=job, source=stored, extraction=report, duplicate_kind=duplicate_kind)

        updated = replace(
            stored,
            recovered_text=report.recovered_text,
            adapter_version=report.adapter_version,
            ingested_at=now_utc(),
        )
        self.vault.update_record(updated)
        if report.recovered_text:
            self.vault.store_derivative(updated.source_id, "extracted.txt", report.recovered_text.encode("utf-8"))
        if extracted.dataset is not None:
            payload: dict[str, object] = {
                "dataset_id": extracted.dataset.dataset_id,
                "source_id": extracted.dataset.provenance_source_id,
                "columns": [
                    {"name": col.name, "unit": col.unit, "declared": col.declared}
                    for col in extracted.dataset.schema
                ],
                "rows": [list(row) for row in extracted.dataset.rows],
                "warnings": list(extracted.dataset.warnings),
            }
            self.datasets[extracted.dataset.dataset_id] = payload
            self.persistence.put("datasets", extracted.dataset.dataset_id, payload)
            self.vault.store_derivative(
                updated.source_id,
                "dataset.json",
                json.dumps(payload, sort_keys=True).encode("utf-8"),
            )
        if extracted.pipeline_result is not None:
            self._pipeline_results[updated.source_id] = extracted.pipeline_result
        if extracted.draft is not None:
            self._drafts[updated.source_id] = extracted.draft

        job = self.jobs.transition(job, JobStatus.VALIDATING, checkpoint=extracted.checkpoint)
        self.documents.add(updated)
        job = self.jobs.transition(job, JobStatus.INDEXING, checkpoint=extracted.checkpoint)
        final_status = JobStatus.AVAILABLE
        if report.equation_candidate_count:
            final_status = JobStatus.REVIEW_REQUIRED
        if pdf_extraction_is_under_recovered(updated, job) and classification.workspace_format is WorkspaceFormat.PDF:
            report = replace(report, warnings=(*report.warnings, "UNDER_RECOVERED"))
        job = self.jobs.transition(job, final_status, checkpoint=extracted.checkpoint)
        if report.equation_candidate_count:
            from knowledge.workspace.review_store import save_review_manifest

            samples: tuple[str, ...] = ()
            if extracted.pipeline_result is not None:
                samples = tuple(
                    candidate.raw_text[:160]
                    for candidate in extracted.pipeline_result.equation_candidates[:5]
                )
            save_review_manifest(
                self.vault,
                source_id=updated.source_id,
                equation_candidate_count=report.equation_candidate_count,
                sample_expressions=samples,
            )
        elif final_status is JobStatus.AVAILABLE:
            from knowledge.workspace.review_store import clear_review_manifest

            clear_review_manifest(self.vault, updated.source_id)
        if reprocess:
            self.jobs.prune_for_source(updated.source_id, keep_job_id=job.job_id)
        self.persistence.put("sources", updated.source_id, updated.to_mapping())
        self.persistence.put("jobs", job.job_id, job.to_mapping())
        self.metrics.ingest_accepted += 1
        if duplicate_kind is DuplicateKind.EXACT_DUPLICATE:
            self.metrics.ingest_duplicates += 1
        return IntakeResult(
            job=job,
            source=updated,
            extraction=report,
            duplicate_kind=duplicate_kind,
        )

    def resume(self, job_id: str) -> IntakeResult:
        job = self.jobs.get(job_id)
        source = self.vault.get(job.source_id)
        content = self.vault.retrieve_original(job.source_id)
        return self.ingest(
            content,
            filename=source.filename,
            rights_status=RightsStatus(source.rights_status),
            project_id=source.project_id,
            parent_source_id=source.parent_source_id,
            title=source.title,
            pipeline_version=job.pipeline_version,
            reprocess=True,
        )

    def reprocess(self, source_id: str, *, pipeline_version: str | None = None) -> IntakeResult:
        source = self.vault.get(source_id)
        content = self.vault.retrieve_original(source_id)
        self.metrics.reprocesses += 1
        return self.ingest(
            content,
            filename=source.filename,
            rights_status=RightsStatus(source.rights_status),
            project_id=source.project_id,
            title=source.title,
            pipeline_version=pipeline_version or source.pipeline_version or self.pipeline_version,
            reprocess=True,
        )

    def search(self, query: str, *, project_id: str | None = None) -> UnifiedSearchResult:
        self._ensure_seed_corpus()
        result = self.service.search(query)
        scope = project_id or self.project_id
        if scope == "GLOBAL":
            return result
        allowed = {item.source_id for item in self.vault.list_sources() if item.project_id in {scope, "GLOBAL"}}
        hits = tuple(
            hit
            for hit in result.hits
            if hit.provenance_id in allowed or hit.entity_id in allowed or not hit.provenance_id
        )
        return UnifiedSearchResult(
            query=result.query,
            kind=result.kind,
            hits=hits,
            evidence=result.evidence,
            provenance_ids=tuple(hit.provenance_id for hit in hits if hit.provenance_id),
        )

    def search_documents(self, query: str, *, project_id: str | None = None) -> tuple[DocumentEvidenceHit, ...]:
        return self.documents.search(query, project_id=project_id or self.project_id)

    def list_sources(self) -> tuple[SourceRecord, ...]:
        return self.vault.list_sources()

    def list_jobs(self) -> tuple[IngestionJob, ...]:
        return self.jobs.list_jobs()

    def review_queue(self) -> tuple[ReviewItem, ...]:
        from knowledge.workspace.review_store import load_review_manifest

        items: list[ReviewItem] = []
        seen: set[str] = set()
        for job in self.list_jobs():
            if job.status is not JobStatus.REVIEW_REQUIRED or job.source_id in seen:
                continue
            seen.add(job.source_id)
            source = self.vault.get(job.source_id)
            manifest = load_review_manifest(self.vault, job.source_id)
            if job.source_id in self._pipeline_results:
                result = self._pipeline_results[job.source_id]
                count = len(result.equation_candidates)
                preview = result.equation_candidates[0].raw_text[:160] if result.equation_candidates else ""
            elif manifest is not None:
                count = manifest.equation_candidate_count
                preview = manifest.sample_expressions[0] if manifest.sample_expressions else ""
            else:
                count = 0
                preview = ""
            items.append(
                ReviewItem(
                    source_id=job.source_id,
                    candidate_id="DOCUMENT",
                    title=source.title or source.filename,
                    expression=(
                        f"{count} engineering relation(s) extracted"
                        + (f" — e.g. {preview}" if preview else "")
                    ),
                    validation_state="REVIEW_REQUIRED",
                ),
            )
        return tuple(items)

    def approve_source(self, source_id: str) -> IngestionJob:
        """Accept a whole document into governed knowledge without per-equation clicks."""

        self.authz.authorize(self.role, WorkspaceAction.APPROVE, actor_id=self.actor_id)
        job = self.jobs.find_latest_for_source(source_id)
        if job is None:
            raise KeyError(f"no job for source '{source_id}'")
        source = self.vault.get(source_id)

        if source_id in self._pipeline_results:
            from knowledge.foundation.equation_approval import EquationReviewDecision

            result = self._pipeline_results[source_id]
            for candidate in result.equation_candidates:
                try:
                    self.service.approve_real_equation(
                        result,
                        candidate.candidate_id,
                        EquationReviewDecision.APPROVE,
                        reference_id=f"REF-{source.sha256[:16]}",
                        title=source.title,
                    )
                except Exception:
                    continue

        job = self.jobs.transition(job, JobStatus.AVAILABLE, checkpoint=job.checkpoint)
        self.jobs.prune_for_source(source_id, keep_job_id=job.job_id)
        updated = replace(source, integrity_status="APPROVED", ingested_at=now_utc())
        self.vault.update_record(updated)
        self.documents.add(updated)
        from knowledge.workspace.review_store import clear_review_manifest

        clear_review_manifest(self.vault, source_id)
        self.persistence.put("sources", source_id, updated.to_mapping())
        self.persistence.put("jobs", job.job_id, job.to_mapping())
        self.metrics.reviews += 1
        return job

    def review_equation(
        self,
        source_id: str,
        candidate_id: str,
        decision: EquationReviewDecision,
    ) -> NormalizedEquationCandidate:
        self._ensure_seed_corpus()
        self.authz.authorize(
            self.role,
            WorkspaceAction.APPROVE if decision is EquationReviewDecision.APPROVE else WorkspaceAction.REVIEW,
            actor_id=self.actor_id,
        )
        result = self._pipeline_results[source_id]
        source = self.vault.get(source_id)
        reviewed = self.service.approve_real_equation(
            result,
            candidate_id,
            decision,
            reference_id=f"REF-{source.sha256[:16]}",
            title=source.title,
        )
        self.metrics.reviews += 1
        return reviewed

    def rebuild_indexes(self) -> int:
        count = self.documents.rebuild(self.vault.list_sources())
        self.metrics.index_rebuilds += 1
        return count

    def delete_source(self, source_id: str) -> None:
        self.authz.authorize(self.role, WorkspaceAction.DESTROY, actor_id=self.actor_id)
        self.vault.delete_source(source_id)
        self.jobs.delete_for_source(source_id)
        self.documents.remove(source_id)
        self._pipeline_results.pop(source_id, None)
        self._drafts.pop(source_id, None)
        if hasattr(self.persistence, "delete"):
            self.persistence.delete("sources", source_id)

    def knowledge_graph(self) -> dict[str, object]:
        from knowledge.workspace.graph_view import build_knowledge_graph

        return build_knowledge_graph(self)

    def backup(self, destination: Path | str | None = None) -> Path:
        if self.root is None:
            raise RuntimeError("In-memory workspace cannot write a filesystem backup.")
        if destination is None:
            stamp = now_utc().replace(":", "").replace("+00:00", "Z")
            backups = self.root / "backups"
            backups.mkdir(parents=True, exist_ok=True)
            destination = backups / f"cosmos-knowledge-{stamp}.zip"
        archive = backup_workspace_root(self.root, Path(destination))
        self.metrics.backups += 1
        return archive.archive_path

    def restore(self, archive_path: Path | str) -> None:
        if self.root is None:
            raise RuntimeError("In-memory workspace cannot restore a filesystem backup.")
        closer = getattr(self.persistence, "close", None)
        if callable(closer):
            closer()
        restore_workspace_root(Path(archive_path), self.root)
        self.vault = DurableArtifactVault(self.root / "knowledge_vault")
        self.jobs = JobStore(self.root / "jobs")
        self.persistence = SQLitePersistenceBackend(self.root / "workspace.sqlite")
        self.persistence.migrate()
        self.rebuild_indexes()
        self.metrics.restores += 1

    def health(self) -> dict[str, object]:
        from knowledge.brain.health import workspace_health

        return workspace_health(self)

    def persist_foundation(self, path: Path | str) -> str:
        return self.service.persist(path)

    def _identity(
        self,
        digest: str,
        filename: str,
        *,
        parent_source_id: str | None,
        edition: str | None,
    ) -> tuple[DuplicateKind, int, str | None]:
        hashed = self.vault.find_by_hash(digest)
        named = self.vault.find_by_filename(filename)
        if hashed:
            return DuplicateKind.EXACT_DUPLICATE, hashed[0].version, hashed[0].source_id
        if parent_source_id and edition:
            parent = self.vault.get(parent_source_id)
            return DuplicateKind.NEW_EDITION, parent.version + 1, parent_source_id
        if parent_source_id:
            parent = self.vault.get(parent_source_id)
            return DuplicateKind.NEW_VERSION, parent.version + 1, parent_source_id
        if named:
            latest = named[-1]
            return DuplicateKind.MODIFIED_SOURCE, latest.version + 1, latest.source_id
        return DuplicateKind.NEW_SOURCE, 1, None


def ingest(
    file: bytes,
    *,
    filename: str,
    workspace: KnowledgeWorkspace | None = None,
    rights_status: RightsStatus = RightsStatus.INTERNAL,
    project_id: str | None = None,
    parent_source_id: str | None = None,
    title: str | None = None,
    pipeline_version: str | None = None,
    reprocess: bool = False,
    edition: str | None = None,
) -> IntakeResult:
    active = workspace or KnowledgeWorkspace(service=KnowledgeFoundationService())
    return active.ingest(
        file,
        filename=filename,
        rights_status=rights_status,
        project_id=project_id,
        parent_source_id=parent_source_id,
        title=title,
        pipeline_version=pipeline_version,
        reprocess=reprocess,
        edition=edition,
    )


def _snippet(text: str, token: str, radius: int = 80) -> str:
    lowered = text.lower()
    index = lowered.find(token.lower())
    if index < 0:
        return text[: radius * 2].strip()
    start = max(0, index - radius)
    end = min(len(text), index + len(token) + radius)
    return text[start:end].strip()
