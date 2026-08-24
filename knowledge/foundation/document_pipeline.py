"""Markdown ingest → W3 parse → W4 extract. Never auto-approves."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from knowledge.extraction.correlation_extractor import extract_correlations
from knowledge.extraction.equation import CandidateEquationExtraction
from knowledge.extraction.w4 import ExtractionContext, extract_document, extract_equation_candidates
from knowledge.extraction.w4.models import ExtractionResult
from knowledge.foundation.equation_approval import EquationApprovalPipeline, NormalizedEquationCandidate
from knowledge.ingestion import IngestionArtifactRef, IngestionRequest, SourceFormat
from knowledge.ingestion_adapters import MarkdownIngestionAdapter
from knowledge.models.correlation import Correlation
from knowledge.parsers.w3 import ParseContext, parse_document
from knowledge.parsers.w3.models import StructuredParsedDocument
from knowledge.source import InMemorySourceVault, VaultArtifact, VaultArtifactMetadata
from knowledge.source.integrity import sha256_text_digest

__all__ = ("DocumentKnowledgeDraft", "ingest_markdown_to_candidates")


@dataclass(frozen=True, slots=True, kw_only=True)
class DocumentKnowledgeDraft:
    document_id: str
    source_id: str
    content_hash: str
    parsed: StructuredParsedDocument
    extraction: ExtractionResult
    equation_candidates: tuple[CandidateEquationExtraction, ...]
    normalized_equations: tuple[NormalizedEquationCandidate, ...]
    correlation_candidates: tuple[Correlation, ...]


def ingest_markdown_to_candidates(
    content: str,
    *,
    source_id: str = "SRC-FOUNDATION",
    artifact_id: str = "ART-FOUNDATION",
    reference_id: str = "REF-FOUNDATION",
) -> DocumentKnowledgeDraft:
    digest = sha256_text_digest(content)
    vault = InMemorySourceVault()
    vault.store(
        VaultArtifact(
            source_id=source_id,
            artifact_id=artifact_id,
            content=content.encode("utf-8"),
            content_hash=digest,
            metadata=VaultArtifactMetadata(source_format=SourceFormat.MARKDOWN.value),
        ),
    )
    adapter = MarkdownIngestionAdapter(vault)
    ingestion = adapter.ingest(
        IngestionRequest(
            artifact=IngestionArtifactRef(
                source_id=source_id,
                artifact_id=artifact_id,
                source_format=SourceFormat.MARKDOWN,
                content_hash=digest,
            ),
            adapter_name=adapter.adapter_name,
            adapter_version=adapter.adapter_version,
        ),
    )
    parsed = parse_document(
        ParseContext(ingestion_result=ingestion, normalized_content=content),
    ).parsed_document
    extraction = extract_document(
        ExtractionContext(parsed_document=parsed, normalized_content=content),
    )
    equation_candidates = extract_equation_candidates(
        ExtractionContext(parsed_document=parsed, normalized_content=content),
    )
    pipeline = EquationApprovalPipeline()
    normalized = tuple(pipeline.normalize(candidate) for candidate in equation_candidates)
    correlations = extract_correlations(
        content,
        document_id=parsed.document_id,
        reference_id=reference_id,
    )
    return DocumentKnowledgeDraft(
        document_id=parsed.document_id,
        source_id=source_id,
        content_hash=digest,
        parsed=parsed,
        extraction=extraction,
        equation_candidates=equation_candidates,
        normalized_equations=normalized,
        correlation_candidates=correlations,
    )


def load_markdown_file(path: str | Path) -> str:
    return Path(path).read_text(encoding="utf-8")
