"""Synthetic provenance/approval contracts; never qualified human signoff."""
import hashlib
import json
from dataclasses import replace
from pathlib import Path
from types import SimpleNamespace

from knowledge.foundation.governance import KnowledgeAction
from knowledge.models.assumption import Assumption
from knowledge.models.document import (
    Document,
    DocumentApprovalStatus,
    DocumentType,
    SecurityLevel,
)
from knowledge.models.equation import Equation, EquationCategory, EquationStatus
from knowledge.models.lifecycle import KnowledgeLifecycle, ProvenanceTrace
from knowledge.models.reference import Reference, ReferenceStatus, ReferenceType
from knowledge.workspace.models import SourceRecord

SOURCE_ID = "SRC-p11-synthetic"
CLAIM_ID = "EQ-p11-synthetic"
ROOT = Path(__file__).resolve().parents[2]


def add_knowledge(workspace, *, approved=True, assumptions=True, project="GLOBAL"):
    raw = b"P11 synthetic source contract. Q = k * A * dT / L. Assumption: constant conductivity. Not a measured experiment or accepted engineering model."
    source = SourceRecord(source_id=SOURCE_ID, artifact_id="ART-p11-synthetic", filename="p11-synthetic.txt", media_type="text/plain", extension=".txt",
        size_bytes=len(raw), sha256=hashlib.sha256(raw).hexdigest(), created_at="2026-10-11T00:00:00Z", ingested_at="2026-10-11T00:00:00Z", source_origin="synthetic-contract-fixture",
        rights_status="INTERNAL", license="repository license", classification="TEST_ONLY", version=1, parent_source_id=None, storage_uri="", integrity_status="VERIFIED",
        workspace_format="TXT", project_id=project, recovered_text=raw.decode(), title="P11 synthetic conduction source")
    stored = workspace.vault.store_original(source, raw)
    workspace.vault.update_record(replace(stored, integrity_status="APPROVED" if approved else "VERIFIED"))
    reference = Reference(reference_id="REF-p11-synthetic", title="P11 synthetic contract citation", authors=("Synthetic test author",),
        reference_type=ReferenceType.INTERNAL_DOCUMENT, publication_year=2026, status=ReferenceStatus.APPROVED if approved else ReferenceStatus.DRAFT)
    document = Document(document_id="DOC-p11-synthetic", document_version_id="v1", title=source.title, content=raw.decode(), document_type=DocumentType.INTERNAL_DOCUMENT,
        reference=reference, approval_status=DocumentApprovalStatus.APPROVED if approved else DocumentApprovalStatus.DRAFT, security_level=SecurityLevel.PUBLIC)
    workspace.service.equations.create(Equation(equation_id=CLAIM_ID, equation_name="Synthetic conduction claim", equation_category=EquationCategory.HEAT_TRANSFER, equation_version="1.0.0",
        source_document=document, source_reference=reference, expression="Q = k * A * dT / L", latex_expression="Q = k * A * dT / L", symbolic_expression="Q = k * A * dT / L",
        page_number=1, section="synthetic contract", status=EquationStatus.APPROVED if approved else EquationStatus.DRAFT))
    if approved:
        workspace.service.audit.record(workspace.service.actor, KnowledgeAction.APPROVE, entity_id=CLAIM_ID, payload={"synthetic": True, "independent_acceptance": False})
    if assumptions:
        workspace.service.assumptions.create(Assumption(assumption_id="ASM-p11-synthetic", statement="Synthetic constant conductivity assumption", category="model",
            affected_entity_ids=(CLAIM_ID,), provenance=ProvenanceTrace(source_reference_id=reference.reference_id, document_id=document.document_id, page=1),
            justification="Fixture only", applicability="Synthetic constant isotropic conductivity; no engine-use approval", confidence=.5,
            lifecycle=KnowledgeLifecycle.CANDIDATE, created_by="synthetic test author"))
    return raw


def report_services():
    """Contract stubs use retained real P10 bytes, not native execution proof."""
    here = ROOT / "docs/implementation/evidence/P10_2026-10-11"
    dataset = json.loads((here/"p09-current-dataset.json").read_text())
    receipt = json.loads((here/"analytic-assessment.json").read_text())
    receipt.update(freshness="current", review_intents=[])
    native = json.loads((here/"native-artifacts-final5/occt/status.json").read_text())
    class Comparison:
        freshness = "current"
        def report(self, *_args): return {**receipt, "freshness": self.freshness}
    class Simulation:
        def dataset(self, *_args): return json.loads(json.dumps(dataset))
        def owned(self, *_args): return SimpleNamespace(geometry_job=native["job_id"])
    class Geometry:
        def accepted(self, *_args):
            return SimpleNamespace(snapshot=SimpleNamespace(content_sha256=native["snapshot_id"])), SimpleNamespace(evidence_json=json.dumps(native["qa"], sort_keys=True, allow_nan=False))
    return Comparison(), Simulation(), Geometry(), receipt["report_id"]
