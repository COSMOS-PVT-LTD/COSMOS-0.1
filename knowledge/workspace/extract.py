"""Capability-driven extraction. UNAVAILABLE is never reported as EMPTY."""

from __future__ import annotations

from dataclasses import dataclass
import json
import re

from knowledge.foundation.document_pipeline import DocumentKnowledgeDraft
from knowledge.foundation.knowledge_service import KnowledgeFoundationService
from knowledge.foundation.real_document_pipeline import RealDocumentPipelineResult
from knowledge.ingestion_adapters.exceptions import AdapterExecutionError
from knowledge.ocr.engine import run_ocr
from knowledge.ocr.models import OCRFailure
from knowledge.pdf.models import ExtractionStatus
from knowledge.workspace.classify import Classification
from knowledge.workspace.datasets import (
    DatasetCandidate,
    DatasetColumn,
    extract_csv_dataset,
    extract_json_dataset,
    extract_xml_text,
)
from knowledge.workspace.models import (
    ExtractionReport,
    ExtractionStageReport,
    JobCheckpoint,
    StageStatus,
    WorkspaceFormat,
)
from knowledge.workspace.office import (
    extract_docx_text,
    extract_epub_text,
    extract_html_text,
    extract_pptx_text,
    extract_xlsx_cells,
)

__all__ = ("UnifiedExtraction", "extract_upload")

_CELL_REF = re.compile(r"^([A-Z]+)(\d+)$")


@dataclass(frozen=True, slots=True, kw_only=True)
class UnifiedExtraction:
    report: ExtractionReport
    dataset: DatasetCandidate | None = None
    pipeline_result: RealDocumentPipelineResult | None = None
    draft: DocumentKnowledgeDraft | None = None
    checkpoint: JobCheckpoint = JobCheckpoint()


def extract_upload(
    content: bytes,
    classification: Classification,
    *,
    source_id: str,
    document_id: str,
    title: str,
    filename: str,
    reference_id: str,
    service: KnowledgeFoundationService,
    checkpoint: JobCheckpoint | None = None,
) -> UnifiedExtraction:
    del checkpoint
    fmt = classification.workspace_format
    if fmt is WorkspaceFormat.PDF:
        return _extract_pdf(
            content,
            source_id=source_id,
            document_id=document_id,
            title=title,
            filename=filename,
            reference_id=reference_id,
            service=service,
        )
    if fmt is WorkspaceFormat.CSV:
        return _extract_csv(content, source_id=source_id)
    if fmt is WorkspaceFormat.JSON:
        return _extract_json(content, source_id=source_id)
    if fmt is WorkspaceFormat.XML:
        return _extract_xml(content)
    if fmt in {WorkspaceFormat.TXT, WorkspaceFormat.MARKDOWN, WorkspaceFormat.LATEX}:
        return _extract_text(
            content,
            source_id=source_id,
            document_id=document_id,
            reference_id=reference_id,
            service=service,
            latex=fmt is WorkspaceFormat.LATEX,
        )
    try:
        if fmt is WorkspaceFormat.HTML:
            return _from_text(extract_html_text(content), adapter_version="workspace-html-1.0.0")
        if fmt is WorkspaceFormat.DOCX:
            return _from_text(extract_docx_text(content), adapter_version="workspace-docx-1.0.0")
        if fmt is WorkspaceFormat.PPTX:
            return _from_text(extract_pptx_text(content), adapter_version="workspace-pptx-1.0.0")
        if fmt is WorkspaceFormat.XLSX:
            return _extract_xlsx(content, source_id=source_id)
        if fmt is WorkspaceFormat.EPUB:
            return _from_text(extract_epub_text(content), adapter_version="workspace-epub-1.0.0")
    except (AdapterExecutionError, ValueError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        return UnifiedExtraction(
            report=ExtractionReport(
                stages=(
                    ExtractionStageReport(name="text", status=StageStatus.FAILED, detail=str(exc)),
                ),
                warnings=(str(exc),),
            ),
        )
    if fmt in {WorkspaceFormat.PNG, WorkspaceFormat.JPEG, WorkspaceFormat.TIFF, WorkspaceFormat.WEBP}:
        return _extract_image(content, source_id=source_id, document_id=document_id)
    return UnifiedExtraction(
        report=ExtractionReport(
            stages=(
                ExtractionStageReport(
                    name="classifier",
                    status=StageStatus.FAILED,
                    detail="UNSUPPORTED_FORMAT",
                ),
            ),
            warnings=("UNSUPPORTED_FORMAT",),
        ),
    )


def _extract_pdf(
    content: bytes,
    *,
    source_id: str,
    document_id: str,
    title: str,
    filename: str,
    reference_id: str,
    service: KnowledgeFoundationService,
) -> UnifiedExtraction:
    result = service.ingest_real_pdf(
        content,
        source_id=source_id,
        document_id=document_id,
        title=title,
        filename=filename,
        reference_id=reference_id,
        author="COSMOS",
    )
    diagnostics = result.extraction.diagnostics if result.extraction is not None else None
    text_status = _pdf_text_status(result.status)
    ocr_status = _ocr_stage_from_pdf(result)
    math_status = _math_stage_from_pdf(result)
    recovered = result.recovered_text
    if text_status is StageStatus.UNAVAILABLE and not recovered.strip():
        recovered = ""
    warnings = tuple(diagnostics.warnings) if diagnostics is not None else ()
    if result.status is ExtractionStatus.EXTRACTION_UNAVAILABLE:
        warnings = (*warnings, "EXTRACTION_UNAVAILABLE")
    report = ExtractionReport(
        stages=(
            ExtractionStageReport(name="text", status=text_status, detail=result.status.value),
            ExtractionStageReport(name="ocr", status=ocr_status, detail="pdf-ocr"),
            ExtractionStageReport(name="math_ocr", status=math_status, detail="tesseract-equation-span-adapter"),
            ExtractionStageReport(
                name="equations",
                status=StageStatus.COMPLETED if result.equation_candidates else StageStatus.PARTIAL,
                detail=str(len(result.equation_candidates)),
            ),
        ),
        recovered_text=recovered,
        equation_candidate_count=len(result.equation_candidates),
        adapter_version="real-document-pipeline",
        warnings=warnings,
    )
    page_count = diagnostics.page_count if diagnostics is not None else 0
    return UnifiedExtraction(
        report=report,
        pipeline_result=result,
        checkpoint=JobCheckpoint(last_completed_page=page_count, last_completed_stage="pdf"),
    )


def _extract_csv(content: bytes, *, source_id: str) -> UnifiedExtraction:
    dataset = extract_csv_dataset(content, source_id=source_id, dataset_id=f"DS-{source_id}")
    text = "\n".join(",".join(row) for row in ((tuple(col.name for col in dataset.schema),) + dataset.rows))
    return UnifiedExtraction(
        report=ExtractionReport(
            stages=(
                ExtractionStageReport(name="text", status=StageStatus.PARTIAL, detail="csv-as-table"),
                ExtractionStageReport(name="datasets", status=StageStatus.COMPLETED, detail=str(dataset.row_count)),
            ),
            recovered_text=text,
            dataset_id=dataset.dataset_id,
            adapter_version="workspace-csv-1.0.0",
            warnings=dataset.warnings,
        ),
        dataset=dataset,
        checkpoint=JobCheckpoint(last_completed_row=dataset.row_count, last_completed_stage="csv"),
    )


def _extract_json(content: bytes, *, source_id: str) -> UnifiedExtraction:
    dataset = extract_json_dataset(content, source_id=source_id, dataset_id=f"DS-{source_id}")
    if dataset is not None:
        return UnifiedExtraction(
            report=ExtractionReport(
                stages=(
                    ExtractionStageReport(name="text", status=StageStatus.PARTIAL, detail="json-dataset"),
                    ExtractionStageReport(name="datasets", status=StageStatus.COMPLETED, detail=str(dataset.row_count)),
                ),
                recovered_text=json.dumps([dict(zip((col.name for col in dataset.schema), row, strict=True)) for row in dataset.rows], sort_keys=True),
                dataset_id=dataset.dataset_id,
                adapter_version="workspace-json-1.0.0",
            ),
            dataset=dataset,
            checkpoint=JobCheckpoint(last_completed_row=dataset.row_count, last_completed_stage="json"),
        )
    text = json.dumps(json.loads(content.decode("utf-8")), indent=2, sort_keys=True)
    return UnifiedExtraction(
        report=ExtractionReport(
            stages=(
                ExtractionStageReport(name="text", status=StageStatus.PARTIAL, detail="json-object"),
                ExtractionStageReport(name="datasets", status=StageStatus.SKIPPED, detail="not a list of objects"),
            ),
            recovered_text=text,
            adapter_version="workspace-json-1.0.0",
        ),
        checkpoint=JobCheckpoint(last_completed_stage="json"),
    )


def _extract_xml(content: bytes) -> UnifiedExtraction:
    text = extract_xml_text(content)
    return UnifiedExtraction(
        report=ExtractionReport(
            stages=(
                ExtractionStageReport(name="text", status=StageStatus.COMPLETED, detail="xml-text"),
                ExtractionStageReport(name="datasets", status=StageStatus.PARTIAL, detail="xml-is-not-auto-mapped"),
            ),
            recovered_text=text,
            adapter_version="workspace-xml-1.0.0",
        ),
        checkpoint=JobCheckpoint(last_completed_stage="xml"),
    )


def _extract_text(
    content: bytes,
    *,
    source_id: str,
    document_id: str,
    reference_id: str,
    service: KnowledgeFoundationService,
    latex: bool,
) -> UnifiedExtraction:
    text = content.decode("utf-8")
    draft = service.ingest_markdown(
        text,
        source_id=source_id,
        artifact_id=document_id,
        reference_id=reference_id,
    )
    return UnifiedExtraction(
        report=ExtractionReport(
            stages=(
                ExtractionStageReport(name="text", status=StageStatus.COMPLETED, detail="utf-8"),
                ExtractionStageReport(
                    name="equations",
                    status=StageStatus.COMPLETED if draft.equation_candidates else StageStatus.PARTIAL,
                    detail=str(len(draft.equation_candidates)),
                ),
                ExtractionStageReport(
                    name="math_ocr",
                    status=StageStatus.SKIPPED if not latex else StageStatus.PARTIAL,
                    detail="source-text-not-compiled" if latex else "not-an-image",
                ),
            ),
            recovered_text=text,
            equation_candidate_count=len(draft.equation_candidates),
            adapter_version="workspace-text-1.0.0",
        ),
        draft=draft,
        checkpoint=JobCheckpoint(last_completed_stage="text"),
    )


def _from_text(text: str, *, adapter_version: str) -> UnifiedExtraction:
    status = StageStatus.COMPLETED if text.strip() else StageStatus.FAILED
    return UnifiedExtraction(
        report=ExtractionReport(
            stages=(ExtractionStageReport(name="text", status=status, detail=adapter_version),),
            recovered_text=text,
            adapter_version=adapter_version,
        ),
        checkpoint=JobCheckpoint(last_completed_stage="text"),
    )


def _extract_xlsx(content: bytes, *, source_id: str) -> UnifiedExtraction:
    cells = extract_xlsx_cells(content)
    dataset = dataset_from_xlsx_cells(cells, source_id=source_id, dataset_id=f"DS-{source_id}")
    text = "\n".join(f"{item['cell']}={item['value']}" for item in cells)
    return UnifiedExtraction(
        report=ExtractionReport(
            stages=(
                ExtractionStageReport(name="text", status=StageStatus.PARTIAL, detail="xlsx-cells"),
                ExtractionStageReport(
                    name="datasets",
                    status=StageStatus.COMPLETED if dataset is not None else StageStatus.PARTIAL,
                    detail=str(dataset.row_count if dataset else 0),
                ),
            ),
            recovered_text=text,
            dataset_id=dataset.dataset_id if dataset else None,
            adapter_version="workspace-xlsx-1.0.0",
        ),
        dataset=dataset,
        checkpoint=JobCheckpoint(
            last_completed_row=dataset.row_count if dataset else 0,
            last_completed_stage="xlsx",
        ),
    )


def _extract_image(content: bytes, *, source_id: str, document_id: str) -> UnifiedExtraction:
    result = run_ocr(
        content,
        source_id=source_id,
        document_id=document_id,
        page_number=1,
        image_id=f"{source_id}-img",
    )
    if result.failure is OCRFailure.OCR_UNAVAILABLE:
        ocr_status = StageStatus.UNAVAILABLE
        detail = "OCR_UNAVAILABLE"
        text = ""
    elif result.failure is not None:
        ocr_status = StageStatus.FAILED
        detail = result.failure.value
        text = ""
    else:
        ocr_status = StageStatus.COMPLETED
        detail = result.adapter_name
        text = result.text
    return UnifiedExtraction(
        report=ExtractionReport(
            stages=(
                ExtractionStageReport(name="images", status=StageStatus.COMPLETED, detail="original-retained"),
                ExtractionStageReport(name="ocr", status=ocr_status, detail=detail),
                ExtractionStageReport(name="text", status=ocr_status, detail=detail),
            ),
            recovered_text=text,
            adapter_version=result.adapter_version,
            warnings=() if ocr_status is not StageStatus.UNAVAILABLE else ("OCR_UNAVAILABLE",),
        ),
        checkpoint=JobCheckpoint(last_completed_page=1, last_completed_stage="image-ocr"),
    )


def dataset_from_xlsx_cells(
    cells: tuple[dict[str, str], ...],
    *,
    source_id: str,
    dataset_id: str,
) -> DatasetCandidate | None:
    parsed: dict[tuple[int, int], str] = {}
    for item in cells:
        match = _CELL_REF.match(item["cell"].upper())
        if not match:
            continue
        parsed[(_column_index(match.group(1)), int(match.group(2)))] = item["value"]
    if not parsed:
        return None
    max_col = max(col for col, _row in parsed)
    max_row = max(row for _col, row in parsed)
    headers = tuple(parsed.get((col, 1), f"col_{col}") for col in range(max_col + 1))
    schema = tuple(DatasetColumn(name=name, unit=None, declared=False) for name in headers)
    rows = []
    for row in range(2, max_row + 1):
        rows.append(tuple(parsed.get((col, row), "") for col in range(max_col + 1)))
    return DatasetCandidate(
        dataset_id=dataset_id,
        schema=schema,
        rows=tuple(rows),
        provenance_source_id=source_id,
    )


def _column_index(letters: str) -> int:
    value = 0
    for char in letters:
        value = value * 26 + (ord(char) - 64)
    return value - 1


def _pdf_text_status(status: ExtractionStatus) -> StageStatus:
    if status is ExtractionStatus.TEXT_AVAILABLE:
        return StageStatus.COMPLETED
    if status is ExtractionStatus.EXTRACTION_UNAVAILABLE:
        return StageStatus.UNAVAILABLE
    if status is ExtractionStatus.RIGHTS_BLOCKED:
        return StageStatus.BLOCKED
    return StageStatus.FAILED


def _ocr_stage_from_pdf(result: RealDocumentPipelineResult) -> StageStatus:
    if result.status is ExtractionStatus.RIGHTS_BLOCKED:
        return StageStatus.BLOCKED
    if result.ocr_evidence:
        return StageStatus.COMPLETED
    diagnostics = result.extraction.diagnostics if result.extraction is not None else None
    if diagnostics is not None and diagnostics.ocr_pages:
        return StageStatus.PARTIAL
    return StageStatus.SKIPPED


def _math_stage_from_pdf(result: RealDocumentPipelineResult) -> StageStatus:
    if not result.math_ocr_results:
        return StageStatus.SKIPPED
    if any(item.failure is None and item.latex for item in result.math_ocr_results):
        return StageStatus.PARTIAL
    return StageStatus.UNAVAILABLE
