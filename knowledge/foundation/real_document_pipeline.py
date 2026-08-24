"""Real PDF → candidates → provenance → validation. Never auto-approves."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
import time

from knowledge.equations.conflicts import detect_equation_conflicts, detect_representation_conflicts
from knowledge.equations.detector import detect_source_equations, extract_explicit_constants
from knowledge.equations.entities import EntityCandidate, extract_entity_candidates
from knowledge.equations.models import SourceEquationCandidate, ValidatedEquationCandidate
from knowledge.equations.reconstruction import EquationReconstruction, reconstruct_equation
from knowledge.equations.review import EquationReviewPackage, build_review_package
from knowledge.equations.validation import validate_equation_candidate
from knowledge.extraction.constant_extractor import ConstantCandidate
from knowledge.extraction.variable_extractor import VariableCandidate, extract_variable_candidates
from knowledge.mathocr.engine import run_math_ocr
from knowledge.mathocr.models import MathOCRResult
from knowledge.models.lifecycle import ProvenanceTrace
from knowledge.ocr.ambiguity import ocr_ambiguity_warnings
from knowledge.ocr.engine import TERMINAL_OCR_FAILURES
from knowledge.ocr.evidence import OCREvidence, build_ocr_evidence
from knowledge.ocr.models import OCRResult
from knowledge.ocr.rasterize import RasterizeResult, rasterize_page
from knowledge.ocr.security import validate_pdf_bytes
from knowledge.ocr.service import OCRJob, OCRService
from knowledge.pdf.extractor import extract_pdf_pages
from knowledge.pdf.models import (
    ExtractionStatus,
    PageClassification,
    PageExtraction,
    PdfDiagnostics,
    PdfExtractionResult,
)
from knowledge.pdf.registry import DuplicateKind, RegisteredSource, SourceModifiedError, SourceRegistry
from knowledge.pdf.structure import ExtractedDocumentStructure, extract_document_structure
from knowledge.references.document_class import DocumentClass
from knowledge.references.rights import RightsStatus, rights_allow_ingestion
from knowledge.source.exceptions import IntegrityMismatchError
from knowledge.validation.contradiction import ConflictRecord

__all__ = (
    "PipelineEvent",
    "PipelineEventKind",
    "PipelineTimings",
    "RealDocumentPipelineResult",
    "run_real_document_pipeline",
)


class PipelineEventKind(Enum):
    SOURCE_REGISTERED = "SOURCE_REGISTERED"
    INGESTION_STARTED = "INGESTION_STARTED"
    INGESTION_COMPLETED = "INGESTION_COMPLETED"
    PAGE_EXTRACTION_COMPLETED = "PAGE_EXTRACTION_COMPLETED"
    OCR_STARTED = "OCR_STARTED"
    OCR_COMPLETED = "OCR_COMPLETED"
    CANDIDATE_EXTRACTED = "CANDIDATE_EXTRACTED"
    CANONICAL_ENTITY_CREATED = "CANONICAL_ENTITY_CREATED"
    PROVENANCE_ATTACHED = "PROVENANCE_ATTACHED"
    VALIDATION_STARTED = "VALIDATION_STARTED"
    VALIDATION_FAILED = "VALIDATION_FAILED"
    REVIEW_REQUIRED = "REVIEW_REQUIRED"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    PERSISTED = "PERSISTED"
    INDEXED = "INDEXED"
    HASH_MISMATCH = "HASH_MISMATCH"
    EXTRACTION_UNAVAILABLE = "EXTRACTION_UNAVAILABLE"
    CONTRADICTION_DETECTED = "CONTRADICTION_DETECTED"
    RIGHTS_BLOCKED = "RIGHTS_BLOCKED"
    MATH_OCR_STARTED = "MATH_OCR_STARTED"
    MATH_OCR_COMPLETED = "MATH_OCR_COMPLETED"
    DATABASE_UNAVAILABLE = "DATABASE_UNAVAILABLE"


@dataclass(frozen=True, slots=True, kw_only=True)
class PipelineEvent:
    kind: PipelineEventKind
    entity_id: str
    detail: str


@dataclass(frozen=True, slots=True, kw_only=True)
class PipelineTimings:
    ingestion_ms: float
    parsing_ms: float
    ocr_ms: float
    math_ocr_ms: float
    extraction_ms: float
    canonicalization_ms: float
    validation_ms: float
    persistence_ms: float
    indexing_ms: float
    search_ms: float


@dataclass(frozen=True, slots=True, kw_only=True)
class RealDocumentPipelineResult:
    registered: RegisteredSource | None
    extraction: PdfExtractionResult | None
    structure: ExtractedDocumentStructure | None
    equation_candidates: tuple[SourceEquationCandidate, ...]
    validated_equations: tuple[ValidatedEquationCandidate, ...]
    review_packages: tuple[EquationReviewPackage, ...]
    variable_candidates: tuple[VariableCandidate, ...]
    constant_candidates: tuple[ConstantCandidate, ...]
    entity_candidates: tuple[EntityCandidate, ...]
    conflicts: tuple[ConflictRecord, ...]
    ocr_results: tuple[OCRResult, ...]
    raster_pages: tuple[RasterizeResult, ...]
    ocr_evidence: tuple[OCREvidence, ...]
    events: tuple[PipelineEvent, ...]
    timings: PipelineTimings
    status: ExtractionStatus
    authoritative: bool = False
    math_ocr_results: tuple[MathOCRResult, ...] = ()
    reconstructions: tuple[EquationReconstruction, ...] = ()
    ocr_jobs: tuple[OCRJob, ...] = ()
    rights_status: RightsStatus | None = None
    document_class: DocumentClass | None = None

    @property
    def recovered_text(self) -> str:
        if self.extraction is None:
            return ""
        return "\n".join(page.text for page in self.extraction.pages if page.text.strip())


def run_real_document_pipeline(
    content: bytes,
    *,
    source_id: str,
    document_id: str,
    title: str,
    filename: str,
    reference_id: str,
    registry: SourceRegistry | None = None,
    expected_hash: str | None = None,
    publisher: str | None = None,
    author: str | None = None,
    edition: str | None = None,
    revision: str | None = None,
    rights_status: RightsStatus | None = None,
    document_class: DocumentClass | None = None,
    license: str | None = None,
    organization: str | None = None,
    publication_year: int | None = None,
    usage_constraints: str | None = None,
) -> RealDocumentPipelineResult:
    events: list[PipelineEvent] = []
    timings_raw = {
        "ingestion_ms": 0.0,
        "parsing_ms": 0.0,
        "ocr_ms": 0.0,
        "math_ocr_ms": 0.0,
        "extraction_ms": 0.0,
        "canonicalization_ms": 0.0,
        "validation_ms": 0.0,
        "persistence_ms": 0.0,
        "indexing_ms": 0.0,
        "search_ms": 0.0,
    }
    source_registry = registry or SourceRegistry()
    events.append(_event(PipelineEventKind.INGESTION_STARTED, source_id, filename))
    security = validate_pdf_bytes(content)
    if not security.accepted:
        events.append(_event(PipelineEventKind.EXTRACTION_UNAVAILABLE, source_id, security.reason))
        return _empty(
            events,
            timings_raw,
            security.status or ExtractionStatus.CORRUPT_SOURCE,
            registered=None,
        )

    resolved_rights = rights_status or RightsStatus.INTERNAL
    resolved_class = document_class or DocumentClass.COSMOS_INTERNAL
    if not rights_allow_ingestion(resolved_rights):
        events.append(_event(PipelineEventKind.RIGHTS_BLOCKED, source_id, resolved_rights.value))
        return _empty(
            events,
            timings_raw,
            ExtractionStatus.RIGHTS_BLOCKED,
            registered=None,
            rights_status=resolved_rights,
            document_class=resolved_class,
        )

    started = time.perf_counter()
    try:
        registered = source_registry.register(
            content,
            source_id=source_id,
            document_id=document_id,
            title=title,
            filename=filename,
            publisher=publisher,
            author=author,
            edition=edition,
            revision=revision,
            rights_status=resolved_rights,
            document_class=resolved_class,
            license=license,
            organization=organization,
            publication_year=publication_year,
            usage_constraints=usage_constraints,
        )
    except SourceModifiedError as exc:
        timings_raw["ingestion_ms"] = (time.perf_counter() - started) * 1000.0
        events.append(_event(PipelineEventKind.HASH_MISMATCH, source_id, str(exc)))
        return _empty(
            events,
            timings_raw,
            ExtractionStatus.HASH_MISMATCH,
            registered=None,
        )
    timings_raw["ingestion_ms"] = (time.perf_counter() - started) * 1000.0
    events.append(
        _event(
            PipelineEventKind.SOURCE_REGISTERED,
            source_id,
            registered.duplicate_kind.value,
        ),
    )
    if registered.duplicate_kind in {
        DuplicateKind.EXACT_DUPLICATE,
        DuplicateKind.SAME_CONTENT_DIFFERENT_FILENAME,
    }:
        events.append(
            _event(PipelineEventKind.INGESTION_COMPLETED, source_id, registered.duplicate_kind.value),
        )

    started = time.perf_counter()
    try:
        extraction = extract_pdf_pages(
            content,
            source_id=source_id,
            document_id=document_id,
            expected_hash=expected_hash or registered.content_hash,
        )
    except IntegrityMismatchError as exc:
        timings_raw["parsing_ms"] = (time.perf_counter() - started) * 1000.0
        events.append(_event(PipelineEventKind.HASH_MISMATCH, source_id, str(exc)))
        return _empty(
            events,
            timings_raw,
            ExtractionStatus.HASH_MISMATCH,
            registered=registered,
        )
    timings_raw["parsing_ms"] = (time.perf_counter() - started) * 1000.0
    events.append(
        _event(
            PipelineEventKind.PAGE_EXTRACTION_COMPLETED,
            document_id,
            f"pages={extraction.diagnostics.page_count}",
        ),
    )

    ocr_results, pages, raster_pages, evidence, ocr_jobs = _maybe_ocr(content, extraction, events, timings_raw)
    with_text = sum(1 for page in pages if page.char_count > 0)
    ocr_used = bool(ocr_results)
    status = (
        ExtractionStatus.HASH_MISMATCH
        if extraction.status is ExtractionStatus.HASH_MISMATCH
        else ExtractionStatus.TEXT_AVAILABLE
        if with_text
        else ExtractionStatus.EXTRACTION_UNAVAILABLE
    )
    method = extraction.method
    if ocr_used and with_text and extraction.method in {"none", "tj-operator"} and not any(
        page.classification.value == "NATIVE_TEXT" for page in pages if page.char_count
    ):
        method = "ocr-tesseract" if any(item.adapter_name.endswith("tesseract") for item in ocr_results) else "ocr"
    elif ocr_used and with_text:
        method = f"{extraction.method}+ocr"
    diagnostics = PdfDiagnostics(
        page_count=len(pages),
        pages_with_text=with_text,
        pages_without_text=len(pages) - with_text,
        pages_with_images=sum(1 for page in pages if page.has_images),
        pages_with_tables=sum(1 for page in pages if "table" in page.text.lower()),
        pages_with_equation_candidates=sum(1 for page in pages if "=" in page.text),
        ocr_pages=len(ocr_results),
        failed_pages=sum(1 for page in pages if not page.char_count and page.warning),
        warnings=tuple(page.warning for page in pages if page.warning)
        + tuple(note for item in evidence for note in item.warnings),
    )
    extraction = PdfExtractionResult(
        source_id=extraction.source_id,
        document_id=extraction.document_id,
        content_hash=extraction.content_hash,
        status=status,
        pages=pages,
        diagnostics=diagnostics,
        method=method,
        elapsed_ms=extraction.elapsed_ms,
    )
    if extraction.status is ExtractionStatus.HASH_MISMATCH:
        events.append(_event(PipelineEventKind.HASH_MISMATCH, source_id, "hash mismatch"))
        return _empty(
            events,
            timings_raw,
            ExtractionStatus.HASH_MISMATCH,
            registered=registered,
            extraction=extraction,
            ocr_results=ocr_results,
            raster_pages=raster_pages,
            ocr_evidence=evidence,
        )
    if extraction.status is ExtractionStatus.EXTRACTION_UNAVAILABLE:
        events.append(
            _event(
                PipelineEventKind.EXTRACTION_UNAVAILABLE,
                document_id,
                "no recoverable page text",
            ),
        )
        events.append(_event(PipelineEventKind.INGESTION_COMPLETED, source_id, extraction.status.value))
        return _empty(
            events,
            timings_raw,
            ExtractionStatus.EXTRACTION_UNAVAILABLE,
            registered=registered,
            extraction=extraction,
            ocr_results=ocr_results,
            raster_pages=raster_pages,
            ocr_evidence=evidence,
        )

    started = time.perf_counter()
    structure = extract_document_structure(
        pages,
        document_id=document_id,
        reference_id=reference_id,
    )
    page_pairs = tuple((page.page_number, page.text) for page in pages)
    equations = detect_source_equations(
        page_pairs,
        source_id=source_id,
        document_id=document_id,
        reference_id=reference_id,
        method=extraction.method,
    )
    recovered = "\n".join(text for _page, text in page_pairs)
    variables = extract_variable_candidates(
        " ".join(item.raw_text for item in equations) or recovered,
        document_id=document_id,
        reference_id=reference_id,
    )
    constants = _explicit_constants(
        recovered,
        document_id=document_id,
        reference_id=reference_id,
    )
    entities = extract_entity_candidates(
        page_pairs,
        document_id=document_id,
        reference_id=reference_id,
    )
    reconstructions = tuple(
        reconstruct_equation(equation.candidate_id, equation.raw_text) for equation in equations
    )
    started_math = time.perf_counter()
    events.append(_event(PipelineEventKind.MATH_OCR_STARTED, document_id, f"equations={len(equations)}"))
    math_ocr_results = _run_math_ocr(equations, raster_pages, evidence)
    events.append(
        _event(
            PipelineEventKind.MATH_OCR_COMPLETED,
            document_id,
            f"results={len(math_ocr_results)}",
        ),
    )
    timings_raw["math_ocr_ms"] = (time.perf_counter() - started_math) * 1000.0
    timings_raw["extraction_ms"] = (time.perf_counter() - started) * 1000.0
    for equation in equations:
        events.append(_event(PipelineEventKind.CANDIDATE_EXTRACTED, equation.candidate_id, equation.raw_text[:80]))
        events.append(
            _event(
                PipelineEventKind.PROVENANCE_ATTACHED,
                equation.candidate_id,
                equation.provenance.source_reference_id,
            ),
        )

    started = time.perf_counter()
    events.append(_event(PipelineEventKind.VALIDATION_STARTED, document_id, "equation-validation"))
    validated = tuple(validate_equation_candidate(equation) for equation in equations)
    timings_raw["validation_ms"] = (time.perf_counter() - started) * 1000.0
    timings_raw["canonicalization_ms"] = timings_raw["validation_ms"]
    for checked in validated:
        if checked.state.value in {"VALIDATION_FAILURE", "INVALID", "NON_AUTHORITATIVE"}:
            events.append(
                _event(
                    PipelineEventKind.VALIDATION_FAILED,
                    checked.candidate.candidate_id,
                    checked.state.value,
                ),
            )
        else:
            events.append(
                _event(
                    PipelineEventKind.REVIEW_REQUIRED,
                    checked.candidate.candidate_id,
                    checked.state.value,
                ),
            )

    conflicts = detect_equation_conflicts(equations)
    conflicts = conflicts + detect_representation_conflicts(None, None)
    for conflict in conflicts:
        events.append(
            _event(
                PipelineEventKind.CONTRADICTION_DETECTED,
                conflict.left_entity_id,
                conflict.reason,
            ),
        )

    packages = tuple(
        _enrich_review_package(item, evidence, reconstructions, math_ocr_results) for item in validated
    )
    events.append(_event(PipelineEventKind.INGESTION_COMPLETED, source_id, extraction.status.value))
    return RealDocumentPipelineResult(
        registered=registered,
        extraction=extraction,
        structure=structure,
        equation_candidates=equations,
        validated_equations=validated,
        review_packages=packages,
        variable_candidates=variables,
        constant_candidates=constants,
        entity_candidates=entities,
        conflicts=conflicts,
        ocr_results=ocr_results,
        raster_pages=raster_pages,
        ocr_evidence=evidence,
        events=tuple(events),
        timings=PipelineTimings(**timings_raw),
        status=extraction.status,
        authoritative=False,
        math_ocr_results=math_ocr_results,
        reconstructions=reconstructions,
        ocr_jobs=ocr_jobs,
        rights_status=resolved_rights,
        document_class=resolved_class,
    )


def _maybe_ocr(
    content: bytes,
    extraction: PdfExtractionResult,
    events: list[PipelineEvent],
    timings_raw: dict[str, float],
) -> tuple[
    tuple[OCRResult, ...],
    tuple[PageExtraction, ...],
    tuple[RasterizeResult, ...],
    tuple[OCREvidence, ...],
    tuple[OCRJob, ...],
]:
    results: list[OCRResult] = []
    pages: list[PageExtraction] = []
    rasters: list[RasterizeResult] = []
    evidence: list[OCREvidence] = []
    jobs: list[OCRJob] = []
    service = OCRService()
    started = time.perf_counter()
    for page in extraction.pages:
        needs_ocr = page.classification in {
            PageClassification.IMAGE_ONLY,
            PageClassification.OCR_REQUIRED,
        } and not page.text.strip()
        if not needs_ocr:
            pages.append(page)
            continue
        events.append(_event(PipelineEventKind.OCR_STARTED, extraction.document_id, f"page={page.page_number}"))
        raster = rasterize_page(
            content,
            page.page_number,
            source_id=extraction.source_id,
            document_id=extraction.document_id,
        )
        rasters.append(raster)
        job = service.extract_page(
            raster.image,
            source_id=extraction.source_id,
            document_id=extraction.document_id,
            page_number=page.page_number,
            image_id=f"{extraction.document_id}-p{page.page_number}",
        )
        jobs.append(job)
        if job.result is None:
            from knowledge.ocr.models import OCRFailure
            from datetime import datetime, timezone

            ocr = OCRResult(
                document_id=extraction.document_id,
                source_id=extraction.source_id,
                page_number=page.page_number,
                image_id=f"{extraction.document_id}-p{page.page_number}",
                text="",
                confidence=0.0,
                language="und",
                regions=(),
                processing_method="ocr-service",
                adapter_name="cosmos-ocr-service",
                adapter_version="1.0.0",
                timestamp=datetime.now(timezone.utc).isoformat(),
                failure=OCRFailure.OCR_FAILED,
                configuration=(job.error or "failed",),
            )
        else:
            ocr = job.result
        results.append(ocr)
        warnings = ocr_ambiguity_warnings(ocr.text)
        if ocr.failure is not None:
            warnings = warnings + (ocr.failure.value,)
        evidence.append(build_ocr_evidence(raster, ocr, warnings=warnings))
        events.append(
            _event(
                PipelineEventKind.OCR_COMPLETED,
                extraction.document_id,
                ocr.failure.value if ocr.failure else "ok",
            ),
        )
        recoverable = bool(ocr.text.strip()) and ocr.failure not in TERMINAL_OCR_FAILURES
        if recoverable:
            warning = None if not warnings else "; ".join(warnings)
            pages.append(
                PageExtraction(
                    page_number=page.page_number,
                    text=ocr.text,
                    classification=page.classification,
                    has_images=True,
                    char_count=len(ocr.text.strip()),
                    warning=warning,
                ),
            )
        else:
            warning = page.warning or (
                ocr.failure.value if ocr.failure else ExtractionStatus.EXTRACTION_UNAVAILABLE.value
            )
            if raster.warning:
                warning = f"{warning}; {raster.warning}"
            pages.append(
                PageExtraction(
                    page_number=page.page_number,
                    text="",
                    classification=page.classification,
                    has_images=page.has_images or bool(raster.image),
                    char_count=0,
                    warning=warning,
                ),
            )
    timings_raw["ocr_ms"] = (time.perf_counter() - started) * 1000.0
    return tuple(results), tuple(pages), tuple(rasters), tuple(evidence), tuple(jobs)


def _run_math_ocr(
    equations: tuple[SourceEquationCandidate, ...],
    rasters: tuple[RasterizeResult, ...],
    evidence: tuple[OCREvidence, ...],
) -> tuple[MathOCRResult, ...]:
    results: list[MathOCRResult] = []
    for equation in equations:
        raster = next((item for item in rasters if item.page_number == equation.page_number), None)
        image = raster.image if raster is not None else b""
        results.append(
            run_math_ocr(
                image,
                source_id=equation.source_id,
                document_id=equation.document_id,
                page_number=equation.page_number or 1,
                region_id=equation.region_id or equation.candidate_id,
                source_text=equation.raw_text,
            ),
        )
    if not equations and evidence:
        first = evidence[0]
        results.append(
            run_math_ocr(
                first.page_image,
                source_id=first.source_id,
                document_id=first.document_id,
                page_number=first.page_number,
                region_id=f"{first.document_id}-p{first.page_number}-math",
                source_text=first.ocr_text,
            ),
        )
    return tuple(results)


def _enrich_review_package(
    validated: ValidatedEquationCandidate,
    evidence: tuple[OCREvidence, ...],
    reconstructions: tuple[EquationReconstruction, ...] = (),
    math_results: tuple[MathOCRResult, ...] = (),
) -> EquationReviewPackage:
    package = build_review_package(validated)
    match = next((item for item in evidence if item.page_number == package.page_number), None)
    reconstructed = next(
        (item for item in reconstructions if item.source_equation_id == package.candidate_id),
        None,
    )
    math = next(
        (item for item in math_results if item.region_id == validated.candidate.region_id),
        next((item for item in math_results if item.page_number == package.page_number), None),
    )
    limitations: list[str] = []
    if reconstructed is not None:
        limitations.extend(reconstructed.reasons)
    if math is not None and math.failure is not None:
        limitations.append(math.failure.value)
    return EquationReviewPackage(
        candidate_id=package.candidate_id,
        excerpt=package.excerpt,
        page_number=package.page_number,
        source_id=package.source_id,
        document_id=package.document_id,
        validation_state=package.validation_state,
        confidence=package.confidence,
        reasons=package.reasons,
        raw_text=package.raw_text,
        variables=package.variables,
        validated=package.validated,
        page_image_hash=match.image_hash if match else None,
        ocr_text=match.ocr_text if match else package.ocr_text,
        ocr_confidence=match.ocr_confidence if match else None,
        ocr_backend=match.ocr_backend if match else None,
        warnings=match.warnings if match else (),
        normalized_representation=reconstructed.normalized_representation if reconstructed else None,
        math_ocr_text=math.source_representation if math else None,
        latex=reconstructed.latex if reconstructed else package.latex,
        limitations=tuple(limitations),
    )


def _explicit_constants(
    text: str,
    *,
    document_id: str,
    reference_id: str,
) -> tuple[ConstantCandidate, ...]:
    provenance = ProvenanceTrace(
        source_reference_id=reference_id,
        document_id=document_id,
        extraction_method="explicit-source-constant",
    )
    found: list[ConstantCandidate] = []
    for item in extract_explicit_constants(text):
        symbol, value = item.split("=", 1)
        found.append(
            ConstantCandidate(
                extraction_id=f"CONST-SRC-{symbol}",
                symbol=symbol,
                name=symbol,
                value=value,
                unit="",
                document_id=document_id,
                provenance=provenance,
            ),
        )
    return tuple(found)


def _event(kind: PipelineEventKind, entity_id: str, detail: str) -> PipelineEvent:
    return PipelineEvent(kind=kind, entity_id=entity_id, detail=detail)


def _empty(
    events: list[PipelineEvent],
    timings_raw: dict[str, float],
    status: ExtractionStatus,
    *,
    registered: RegisteredSource | None,
    extraction: PdfExtractionResult | None = None,
    ocr_results: tuple[OCRResult, ...] = (),
    raster_pages: tuple[RasterizeResult, ...] = (),
    ocr_evidence: tuple[OCREvidence, ...] = (),
    rights_status: RightsStatus | None = None,
    document_class: DocumentClass | None = None,
) -> RealDocumentPipelineResult:
    return RealDocumentPipelineResult(
        registered=registered,
        extraction=extraction,
        structure=None,
        equation_candidates=(),
        validated_equations=(),
        review_packages=(),
        variable_candidates=(),
        constant_candidates=(),
        entity_candidates=(),
        conflicts=(),
        ocr_results=ocr_results,
        raster_pages=raster_pages,
        ocr_evidence=ocr_evidence,
        events=tuple(events),
        timings=PipelineTimings(**timings_raw),
        status=status,
        authoritative=False,
        rights_status=rights_status,
        document_class=document_class,
    )
