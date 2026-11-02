"""Read-only source-to-equation projection; never invent approval or applicability."""
from __future__ import annotations

import json
import re
from dataclasses import asdict
from typing import Any
from urllib.parse import quote

from knowledge.models.equation import Equation
from knowledge.repository.knowledge_repository import EntityNotFoundError
from knowledge.workspace.session import KnowledgeWorkspace, _document_id_for_source
from knowledge.workspace.vault import VaultError
from systems.contracts.geometry._wire import digest, dumps, require


def identifier(value: Any) -> str:
    require(type(value) is str and re.fullmatch(r"[A-Za-z0-9_.:-]{1,128}", value) is not None,
            "INVALID_IDENTIFIER", "Use an exact bounded repository identifier, not a path or URL")
    return value


class EvidenceNavigation:
    def __init__(self, workspace: KnowledgeWorkspace) -> None:
        self.workspace = workspace

    def _allowed(self, source: Any) -> bool:
        scope = self.workspace.project_id
        return scope == "GLOBAL" or source.project_id in {scope, "GLOBAL"}

    def _source_for(self, equation: Equation) -> Any:
        return next((s for s in self.workspace.list_sources() if self._allowed(s)
                     and _document_id_for_source(s.source_id) == equation.source_document.document_id), None)

    def context(self, query: str = "", offset: int = 0) -> dict[str, Any]:
        require(type(query) is str and len(query) <= 256 and type(offset) is int and 0 <= offset <= 10000,
                "INVALID_QUERY", "Search is limited to 256 characters and bounded integer pages")
        words = query.lower().split()
        sources = [s for s in self.workspace.list_sources() if self._allowed(s)
                   and all(w in (s.title+" "+s.filename).lower() for w in words)]
        claims = [e for e in self.workspace.service.equations.query()
                  if all(w in (e.equation_name+" "+e.expression).lower() for w in words)
                  and (self.workspace.project_id == "GLOBAL" or self._source_for(e) is not None)]
        sources.sort(key=lambda s: s.source_id); claims.sort(key=lambda e: e.equation_id)
        return {"schema_version": "p11-knowledge-context-v1", "project_id": self.workspace.project_id,
                "sources": [{"source_id": s.source_id, "title": s.title or s.filename, "version": s.version,
                             "sha256": s.sha256, "recorded_status": s.integrity_status} for s in sources[offset:offset+20]],
                "claims": [{"claim_id": e.equation_id, "title": e.equation_name, "expression": e.expression,
                            "recorded_status": e.status.value} for e in claims[offset:offset+20]],
                "source_count": len(sources), "claim_count": len(claims), "offset": offset, "page_size": 20,
                "search_scope": "Deterministic title/filename/equation navigation filter; existing semantic search remains in legacy Maharshi",
                "approval_scope": "Recorded knowledge approval is not independent engineering acceptance",
                "provider_invoked": False, "experimental_validation": "not-performed", "production_handoff": False}

    def source(self, source_id: str) -> dict[str, Any]:
        identifier(source_id)
        try:
            source = self.workspace.vault.get(source_id)
        except VaultError as error:
            require(False, "SOURCE_UNAVAILABLE", str(error))
            raise AssertionError("unreachable") from error
        require(self._allowed(source), "SOURCE_UNAVAILABLE", "Source is not in this project scope")
        checked = source.size_bytes <= 4*1024**2
        intact = checked and self.workspace.vault.verify(source_id)
        return {"source_id": source_id, "title": source.title or source.filename, "filename": source.filename,
                "project_id": source.project_id, "version": source.version, "parent_source_id": source.parent_source_id,
                "sha256": source.sha256, "size_bytes": source.size_bytes,
                "integrity": "verified-original-bytes" if intact else "mismatch-or-missing" if checked else "not-checked-preview-size-limit",
                "recorded_status": source.integrity_status, "source_origin": source.source_origin,
                "rights_status": source.rights_status, "license": source.license,
                "excerpt": source.recovered_text[:2048] if intact else "",
                "excerpt_scope": "First 2048 recovered characters; derivative excerpt is not an exact original-page transcription",
                "metadata_url": "/api/sources/"+quote(source_id, safe=""),
                "evidence_url": "/api/knowledge-reports/sources/"+quote(source_id, safe=""),
                "original_available": intact, "recorded_approved": source.integrity_status == "APPROVED",
                "independent_acceptance": False}

    def claim(self, claim_id: str) -> dict[str, Any]:
        identifier(claim_id)
        try:
            equation = self.workspace.service.equations.get(claim_id)
        except EntityNotFoundError as error:
            require(False, "CLAIM_UNAVAILABLE", str(error))
            raise AssertionError("unreachable") from error
        source_record = self._source_for(equation)
        require(self.workspace.project_id == "GLOBAL" or source_record is not None,
                "CLAIM_UNAVAILABLE", "Claim is not bound to a source in this project")
        source = self.source(source_record.source_id) if source_record else None
        events = [asdict(e) for e in self.workspace.service.audit.events() if e.entity_id == claim_id]
        require(len(events) <= 64, "EVIDENCE_LIMIT", "Review history exceeds this bounded preview")
        assumptions = [asdict(a) for a in self.workspace.service.assumptions.query() if claim_id in a.affected_entity_ids]
        require(len(assumptions) <= 32, "EVIDENCE_LIMIT", "Assumptions exceed this bounded preview")
        # Only serialize recorded fields. No invented operating ranges or unit declarations.
        for assumption in assumptions:
            assumption["lifecycle"] = assumption["lifecycle"].value
        approved = equation.status.value == "APPROVED" and source is not None and source["original_available"]
        approved = approved and source is not None and source["recorded_approved"] and bool(events) and events[-1]["action"] == "APPROVE"
        approved = approved and equation.source_reference.status.value == "APPROVED" and equation.source_document.approval_status.value == "APPROVED"
        value = {"schema_version": "p11-claim-v1", "claim_id": claim_id, "title": equation.equation_name,
                 "equation": {"expression": equation.expression, "version": equation.equation_version, "recorded_status": equation.status.value,
                              "category": equation.equation_category.value, "document_id": equation.source_document.document_id,
                              "reference_id": equation.source_reference.reference_id, "page": equation.page_number, "section": equation.section},
                 "citation": {"title": equation.source_reference.title, "authors": list(equation.source_reference.authors),
                              "status": equation.source_reference.status.value},
                 "source": source, "assumptions": assumptions, "review_events": events,
                 "applicability": "Recorded linked assumptions only; simulation-use applicability is not established" if assumptions else "unavailable-no-linked-assumptions",
                 "units": "Inspect source and recorded assumptions; equation unit metadata is not inferred",
                 "source_navigation_status": "recorded-approved-source-and-review" if approved else "evidence-unavailable-or-review-pending",
                 "source_binding": "Exact existing document identity to vault source; not title or semantic similarity",
                 "independent_acceptance": False, "experimental_validation": "not-performed", "production_handoff": False,
                 "evidence_url": "/api/knowledge-reports/claims/"+quote(claim_id, safe="")}
        require(len(str(value)) < 128*1024, "EVIDENCE_LIMIT", "Claim snapshot exceeds this preview")
        raw = dumps(value)
        return {"evidence_sha256": digest(value), "claim": json.loads(raw), "canonical_json": raw}
