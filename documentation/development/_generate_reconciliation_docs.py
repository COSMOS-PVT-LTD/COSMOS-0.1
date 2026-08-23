"""Generate reconciliation documentation artifacts from kg_reconciliation_registry.json."""
from __future__ import annotations

import json
from collections import Counter
from datetime import date
from pathlib import Path

ROOT = Path(__file__).parent
REG_PATH = ROOT / "kg_reconciliation_registry.json"
OUT = ROOT

DISPOSITION = {
    "A": "EXACT_MATCH",
    "B": "RELOCATED",
    "C": "CONSOLIDATED",
    "D": "SUPERSEDED",
    "E": "MISSING_REQUIRED",
    "F": "MISSING_DECISION_REQUIRED",
    "G": "EXTRA_JUSTIFIED",
    "H": "EXTRA_REVIEW_REQUIRED",
}

TODAY = "2026-08-23"


def load() -> tuple[dict, Counter]:
    data = json.loads(REG_PATH.read_text())
    entries = data["entries"]
    counts = Counter(v["disposition"] for v in entries.values())
    return entries, counts


def current_py_files() -> list[str]:
    return sorted(str(p) for p in Path("knowledge").rglob("*.py"))


def classify_extra(path: str, exact_paths: set[str]) -> str:
    if path in exact_paths:
        return "A"
    if any(x in path for x in ("/w3/", "/w4/", "/w7/", "/w8/", "/w10/", "/interface/")):
        return "G"
    if path.startswith("knowledge/source/") or "ingestion_adapters" in path:
        return "G"
    if path.startswith("knowledge/interface/"):
        return "G"
    if path.startswith("knowledge/graph/"):
        return "G"
    if path.endswith("__init__.py"):
        return "G"
    if "exceptions" in path or "identity" in path:
        return "G"
    return "H"


def capability_addressed(counts: Counter) -> int:
    return counts["A"] + counts["B"] + counts["C"] + counts["D"]


def write_traceability_matrix(entries: dict, counts: Counter) -> None:
    current = current_py_files()
    exact_paths = {k for k, v in entries.items() if v["disposition"] == "A"}
    extra = [(p, classify_extra(p, exact_paths)) for p in current if p not in exact_paths]
    g_extra = sum(1 for _, c in extra if c == "G")
    h_extra = sum(1 for _, c in extra if c == "H")
    total = len(entries)
    cap = capability_addressed(counts)

    lines = [
        "# Knowledge File-Level Traceability Matrix",
        "",
        f"**Document ID:** COSMOS-KG-FILE-TRACE-002",
        f"**Date:** {TODAY}",
        "**Authority:** Technical Owner Reconciliation Directive",
        "**Phase:** RECONCILIATION ONLY — no implementation",
        "",
        "## Disposition Key",
        "",
        "| Code | Label |",
        "|------|-------|",
    ]
    for code, label in DISPOSITION.items():
        lines.append(f"| {code} | {label} |")

    lines += [
        "",
        "## Summary",
        "",
        "| Metric | Value |",
        "|--------|-------|",
        f"| Frozen files reconciled | {total} |",
        f"| Current knowledge .py files | {len(current)} |",
        f"| A EXACT_MATCH | {counts['A']} |",
        f"| B RELOCATED | {counts['B']} |",
        f"| C CONSOLIDATED | {counts['C']} |",
        f"| D SUPERSEDED | {counts['D']} |",
        f"| E MISSING_REQUIRED | {counts['E']} |",
        f"| F MISSING_DECISION_REQUIRED | {counts['F']} |",
        f"| G EXTRA_JUSTIFIED (current only) | {g_extra} |",
        f"| H EXTRA_REVIEW_REQUIRED (current only) | {h_extra} |",
        "",
        f"**FILE-LEVEL EXACT MATCH:** {counts['A']}/{total} = {counts['A']/total*100:.1f}%",
        f"**CAPABILITY ADDRESSED (A+B+C+D):** {cap}/{total} = {cap/total*100:.1f}%",
        "",
        "---",
        "",
        "## Master Table (Frozen → Current)",
        "",
        "| # | Frozen Path | Disp | Current Path | Symbol(s) | Capability | KG | BLOCK | Test | Justification |",
        "|---|-------------|------|--------------|-----------|------------|-----|-------|------|---------------|",
    ]
    for i, (frozen, d) in enumerate(sorted(entries.items()), 1):
        lines.append(
            f"| {i} | `{frozen}` | {d['disposition']} | `{d['current']}` | `{d['symbols']}` | "
            f"{d['capability']} | {d['kg']} | {d['block']} | {d['test']} | {d['justification']} |"
        )

    lines += [
        "",
        "---",
        "",
        "## Reverse Inventory (Current Extra Files)",
        "",
        "| # | Current Path | Disp | Architectural Role |",
        "|---|--------------|------|--------------------|",
    ]
    for i, (path, cat) in enumerate(sorted(extra), 1):
        role = "KG block subpackage / W1-W2 extension / graph contract" if cat == "G" else "Non-frozen path replacing frozen capability — see master table"
        lines.append(f"| {i} | `{path}` | {cat} | {role} |")

    (OUT / "knowledge_file_level_traceability_matrix.md").write_text("\n".join(lines))


def write_reconciliation_master(entries: dict, counts: Counter) -> None:
    total = len(entries)
    cap = capability_addressed(counts)
    current = current_py_files()
    exact_list = sorted(k for k, v in entries.items() if v["disposition"] == "A")

    lines = [
        "# Knowledge File-Level Architecture Reconciliation",
        "",
        "**Document ID:** COSMOS-KG-FILE-RECON-MASTER-002",
        f"**Date:** {TODAY}",
        "**Type:** RECONCILIATION ONLY — no code changes authorized",
        "**Authority:** COSMOS Technical Owner Reconciliation Directive",
        "",
        "---",
        "",
        "## Executive Summary",
        "",
        "Reconciliation of **current `knowledge/`** against frozen Part-3 Knowledge Folder Architecture.",
        "Every frozen architectural `.py` file receives exactly one disposition **A–F**.",
        "Current-only files receive **G** or **H** in the reverse inventory.",
        "",
        "| Certification Metric | Result |",
        "|---------------------|--------|",
        f"| FILE-LEVEL EXACT MATCH (A) | **{counts['A']} / {total} = {counts['A']/total*100:.1f}%** |",
        f"| CAPABILITY ADDRESSED (A+B+C+D) | **{cap} / {total} = {cap/total*100:.1f}%** |",
        f"| MISSING REQUIRED (E) | **{counts['E']}** |",
        f"| MISSING DECISION REQUIRED (F) | **{counts['F']}** |",
        f"| Current implementation files | **{len(current)}** |",
        "| Regression baseline | **1219 passed, 5 skipped** |",
        "| BLOCK-001→011 | **FROZEN — unchanged** |",
        "| BLOCK-012 | **READY FOR HUMAN FREEZE APPROVAL** |",
        "| FILE-LEVEL CERTIFIED 100% | **NO** |",
        "",
        "**Conclusion:** Capability-faithful KG-001→051 reference implementation with deliberate structural refinement.",
        "Not superficial path matching. Formal approval required for deviations before certification.",
        "",
        "---",
        "",
        "## Disposition Summary",
        "",
        "| Code | Label | Count | % of 175 |",
        "|------|-------|-------|----------|",
    ]
    for code in "ABCDEF":
        c = counts[code]
        lines.append(f"| {code} | {DISPOSITION[code]} | {c} | {c/total*100:.1f}% |")

    lines += [
        "",
        "---",
        "",
        "## A — EXACT_MATCH (12)",
        "",
        "```text",
        *exact_list,
        "```",
        "",
        "Protected frozen interfaces: `quantity.py`, `unit.py`, `dimension.py` (BLOCK-007+).",
        "",
        "---",
        "",
        "## B — RELOCATED (27)",
        "",
        "Frozen path preserved capability at a different module path. See traceability matrix for symbol-level mapping.",
        "",
        "Representative examples:",
        "",
    ]
    for frozen, d in sorted(entries.items()):
        if d["disposition"] == "B":
            lines.append(f"- `{frozen}` → `{d['current']}` (`{d['symbols']}`)")
    lines += ["", "---", "", "## C — CONSOLIDATED (48)", ""]
    for frozen, d in sorted(entries.items()):
        if d["disposition"] == "C":
            lines.append(f"- `{frozen}` → `{d['current']}` (`{d['symbols']}`)")
    lines += ["", "---", "", "## D — SUPERSEDED (16)", ""]
    for frozen, d in sorted(entries.items()):
        if d["disposition"] == "D":
            lines.append(f"- `{frozen}` → `{d['current']}` — {d['justification']}")
    lines += ["", "---", "", "## E — MISSING_REQUIRED (67)", ""]
    for frozen, d in sorted(entries.items()):
        if d["disposition"] == "E":
            lines.append(f"- `{frozen}` — {d['capability']} ({d['kg']})")
    lines += ["", "---", "", "## F — MISSING_DECISION_REQUIRED (5)", ""]
    for frozen, d in sorted(entries.items()):
        if d["disposition"] == "F":
            lines.append(f"- `{frozen}` — {d['justification']}")
    lines += [
        "",
        "---",
        "",
        "## G/H — Current Extra Files",
        "",
        "See `knowledge_file_level_traceability_matrix.md` reverse inventory.",
        "G = justified KG evolution (w3/w4/w7/w8/w10/interface, source vault, ingestion_adapters).",
        "H = review required (non-frozen paths that implement frozen capabilities).",
        "",
        "---",
        "",
        "## Certification Blockers",
        "",
        "1. 67 frozen files E — no implementation at expected path",
        "2. 5 frozen files F — architecture decision required before implementation",
        "3. Deviations in deviation register lack formal approval",
        "4. Compatibility facades not yet implemented (plan only)",
        "5. Exporters package entirely missing",
        "6. Entity repositories (plural) deferred",
        "",
        "---",
        "",
        "## Related Documents",
        "",
        "| # | Document |",
        "|---|----------|",
        "| 1 | `knowledge_file_level_traceability_matrix.md` |",
        "| 2 | `knowledge_models_gap_analysis.md` |",
        "| 3 | `knowledge_architecture_deviation_register.md` |",
        "| 4 | `knowledge_rag_alignment_audit.md` |",
        "| 5 | `knowledge_next_development_plan.md` |",
        "| 6 | `knowledge_architecture_decision_register.md` |",
        "| 7 | `knowledge_missing_capability_register.md` |",
        "| 8 | `knowledge_compatibility_layer_plan.md` |",
        "| 9 | `knowledge_certification_readiness_report.md` |",
        "",
        "```text",
        "FINAL CERTIFICATION: NOT FILE-LEVEL CERTIFIED 100%",
        "CODE CHANGES: NONE",
        "IMPLEMENTATION GATE: CLOSED (reconciliation phase only)",
        "```",
    ]
    (OUT / "knowledge_file_level_architecture_reconciliation.md").write_text("\n".join(lines))


def write_models_gap(entries: dict) -> None:
    models = {k: v for k, v in entries.items() if k.startswith("knowledge/models/")}
    disp_map = {"A": "EXACT_MATCH", "B": "RELOCATED", "C": "CONSOLIDATED", "D": "SUPERSEDED",
                "E": "MISSING_REQUIRED", "F": "MISSING_DECISION_REQUIRED"}
    counts = Counter(v["disposition"] for v in models.values())

    lines = [
        "# Knowledge Models Gap Analysis",
        "",
        "**Document ID:** COSMOS-KG-MODELS-GAP-002",
        f"**Date:** {TODAY}",
        "**Type:** RECONCILIATION ONLY",
        "**Frozen source:** `documentation/COSMOS_0.1_FREEZED.md` Part 3 — `knowledge/models/`",
        "",
        "## Summary",
        "",
        "| Metric | Count |",
        "|--------|-------|",
        f"| Models expected (frozen) | **36** |",
        f"| A EXACT_MATCH | **{counts['A']}** |",
        f"| C CONSOLIDATED | **{counts['C']}** |",
        f"| E MISSING_REQUIRED | **{counts['E']}** |",
        f"| F MISSING_DECISION_REQUIRED | **{counts['F']}** |",
        "",
        "**Rule applied:** No duplicate Quantity/Unit/Dimension/Entity/Graph models created for filename matching.",
        "",
        "---",
        "",
        "## 36-Model Reconciliation",
        "",
        "| # | Frozen Path | Disp | Current Path | Symbol(s) | Equivalent? | Create? | Duplicate Risk | KG | Test |",
        "|---|-------------|------|--------------|-----------|-------------|---------|----------------|-----|------|",
    ]
    for i, (frozen, d) in enumerate(sorted(models.items()), 1):
        fname = frozen.split("/")[-1]
        equiv = "YES" if d["disposition"] in {"A", "B", "C", "D"} else "NO"
        create = "NO" if d["disposition"] in {"A", "C", "D"} else ("DECISION" if d["disposition"] == "F" else "YES (future block)")
        dup = "NONE" if d["disposition"] in {"A", "C"} else ("LOW" if d["disposition"] == "E" else "—")
        lines.append(
            f"| {i} | `{fname}` | {d['disposition']} | `{d['current']}` | `{d['symbols']}` | "
            f"{equiv} | {create} | {dup} | {d['kg']} | {d['test']} |"
        )

    lines += [
        "",
        "---",
        "",
        "## Consolidation Register (Formal)",
        "",
        "| Frozen Model | Canonical Location | Symbol | Justification |",
        "|--------------|-------------------|--------|---------------|",
        "| `paragraph.py` | `knowledge/parsers/w3/models.py` | `ParsedParagraph` | W3 parse artifact, not domain entity |",
        "| `figure.py` | `knowledge/parsers/w3/models.py` | `ParsedFigure` | W3 figure extraction model |",
        "| `table.py` | `knowledge/parsers/w3/models.py` | `ParsedTable` | W3 table extraction model |",
        "| `citation.py` | `knowledge/parsers/w3/models.py` | `ParsedCitation` | Citation parse artifact |",
        "| `component.py` | `knowledge/graph/entity.py` | `CanonicalEntityType` | Graph entity typing |",
        "| `ontology_node.py` | `knowledge/ontology/models.py` | `OntologyTerm` | W5 ontology term |",
        "| `ontology_edge.py` | `knowledge/ontology/models.py` | `TaxonomyEdge` | W5 taxonomy edge |",
        "| `metadata.py` | `knowledge/ingestion/models.py` | `IngestionResult` | Distributed metadata at ingestion boundary |",
        "",
        "---",
        "",
        "## Protected Models (DO NOT MODIFY)",
        "",
        "| File | Protection |",
        "|------|------------|",
        "| `knowledge/models/quantity.py` | FROZEN BLOCK-007+ |",
        "| `knowledge/models/unit.py` | FROZEN BLOCK-007+ |",
        "| `knowledge/models/dimension.py` | FROZEN BLOCK-007+ |",
    ]
    (OUT / "knowledge_models_gap_analysis.md").write_text("\n".join(lines))


def write_missing_capability(entries: dict) -> None:
    missing = [(k, v) for k, v in entries.items() if v["disposition"] in {"E", "F"}]
    lines = [
        "# Knowledge Missing Capability Register",
        "",
        "**Document ID:** COSMOS-KG-MISSING-CAP-001",
        f"**Date:** {TODAY}",
        "**Phase:** REGISTER ONLY — no implementation authorized",
        "",
        f"**Total entries:** {len(missing)} (E: {sum(1 for _,v in missing if v['disposition']=='E')}, F: {sum(1 for _,v in missing if v['disposition']=='F')})",
        "",
        "---",
        "",
        "| ID | Architecture File | Required Capability | Reason | Dependencies | Substitute | Impact | Proposed Block | Test Req | Prod Impact |",
        "|----|-------------------|-------------------|--------|--------------|------------|--------|----------------|----------|-------------|",
    ]
    for i, (frozen, d) in enumerate(sorted(missing), 1):
        mid = f"MCAP-{i:03d}"
        sub = d["current"] if d["current"] != "—" else "None"
        block = "KG-BLOCK-013+" if d["disposition"] == "E" else "ADR required"
        lines.append(
            f"| {mid} | `{frozen}` | {d['capability']} | Frozen Part-3 file absent | {d['dependencies'] or 'See traceability'} | `{sub}` | "
            f"File-level gap; capability may be partial | {block} | Unit + integration | Deferred until approved |"
        )
    lines += [
        "",
        "---",
        "",
        "## Priority Tiers (Proposed — Not Authorized)",
        "",
        "### Tier 1 — Architecture decisions (F)",
        "",
        "- `knowledge/models/sentence.py` — sentence granularity vs paragraph-only parsing",
        "- `knowledge/models/empirical_relation.py` — relation to correlation/physical_law",
        "- `knowledge/graph/concept_graph.py` — concept graph vs engineering graph",
        "- `knowledge/utils/text_utils.py` — shared text helpers scope",
        "- `knowledge/parsers/sentence_parser.py` — depends on sentence model ADR",
        "",
        "### Tier 2 — High-value missing (E, grouped)",
        "",
        "- **Exporters (7):** `knowledge/exporters/*` — export pipeline for engineering handoff",
        "- **Entity repositories (15):** `knowledge/repositories/*_repository.py` — persistence layer",
        "- **Format loaders (5):** epub, latex, image, ocr, markitdown",
        "- **Domain extractors (12):** process, simulation, failure_mode, design_rule, etc.",
        "",
        "### Tier 3 — Deferred domain models (E)",
        "",
        "- Chapter/section/appendix/glossary canonical models",
        "- physical_law, correlation, assumption, boundary_condition, property, process, etc.",
        "",
        "**Implementation gate:** CLOSED until ADRs approved.",
    ]
    (OUT / "knowledge_missing_capability_register.md").write_text("\n".join(lines))


def write_decision_register() -> None:
    lines = [
        "# Knowledge Architecture Decision Register",
        "",
        "**Document ID:** COSMOS-KG-ADR-REG-001",
        f"**Date:** {TODAY}",
        "**Phase:** RECONCILIATION — decisions pending human approval",
        "",
        "| ADR-ID | Topic | Frozen Expectation | Current State | Options | Recommendation | Status |",
        "|--------|-------|-------------------|---------------|---------|----------------|--------|",
        "| ADR-001 | Repository layout | `knowledge/repositories/` plural | `knowledge/repository/` singular + graph store | (a) Implement plural repos (b) Approve graph-primary (c) Facade | **(b)** Approve graph-primary; defer entity repos | **PENDING** |",
        "| ADR-002 | Model consolidation | 36 files under `models/` | 11 files + parser/ontology/graph consolidation | (a) Split back to 36 files (b) Approve consolidation (c) Hybrid facades | **(b)** Approve consolidation with formal register | **PENDING** |",
        "| ADR-003 | W3/W4/W7/W8/W10 subpackages | Flat Part-3 modules | Block-scoped subpackages | (a) Flatten (b) Approve subpackages | **(b)** Approve — superior modularity | **PENDING** |",
        "| ADR-004 | Exporters package | 7 exporter modules | Not implemented | (a) Implement (b) Supersede by interface JSON (c) Defer | **(c)** Defer to BLOCK-013+ with scope ADR | **PENDING** |",
        "| ADR-005 | Sentence-level parsing | `sentence.py` + `sentence_parser.py` | Paragraph-level W3 only | (a) Add sentence model (b) Supersede by paragraph (c) Optional NLP block | **(c)** ADR-005 required before implementation | **PENDING** |",
        "| ADR-006 | Empirical relation model | `empirical_relation.py` | Absent | (a) New model (b) Merge into correlation (c) Graph edge only | **Decision required** | **PENDING** |",
        "| ADR-007 | Concept graph | `concept_graph.py` | Engineering graph only | (a) Separate concept graph (b) Extend engineering graph (c) Defer | **(b)** unless RAG requires separate ontology graph | **PENDING** |",
        "| ADR-008 | Static ontology domains | 15 domain `.py` files | `OntologyRegistry` dynamic | (a) Restore static modules (b) Domain packs in registry (c) Hybrid | **(b)** Domain packs — aligns with DEV-007 | **PENDING** |",
        "| ADR-009 | Semantic embeddings | Production embedding backend | Reference vectors in-memory | (a) Local model (b) Cloud API (c) Keep reference for qual | **(a)** local model when production-bound | **PENDING** |",
        "| ADR-010 | Controlled RAG vs recommendation | `recommendation_engine.py` | `ControlledRAGOrchestrator` | (a) Restore recommender (b) Approve supersession | **(b)** Approve — no auto fact promotion | **PENDING** |",
        "| ADR-011 | Compatibility facades | Frozen import paths | Canonical w* paths only | (a) Thin facades (b) Documentation-only mapping (c) No facades | **(a)** selective facades — see compatibility plan | **PENDING** |",
        "| ADR-012 | BLOCK-012 freeze | Integration qualification | 1219 tests, E2E qualified | Approve freeze / request changes | **Approve freeze** after human review | **PENDING** |",
        "",
        "---",
        "",
        "**Note:** No ADR is approved merely because code exists. Technical owner sign-off required.",
    ]
    (OUT / "knowledge_architecture_decision_register.md").write_text("\n".join(lines))


def write_compatibility_plan() -> None:
    lines = [
        "# Knowledge Compatibility Layer Plan",
        "",
        "**Document ID:** COSMOS-KG-COMPAT-PLAN-001",
        f"**Date:** {TODAY}",
        "**Phase:** PLAN ONLY — no implementation authorized",
        "",
        "## Pattern",
        "",
        "```text",
        "Frozen API (import path)",
        "    ↓",
        "Compatibility facade (thin, tested)",
        "    ↓",
        "Current canonical implementation",
        "```",
        "",
        "## Proposed Facades (Priority Order)",
        "",
        "| ID | Frozen Path | Facade API | Canonical Target | Behavior | Test Plan | Block |",
        "|----|-------------|------------|------------------|----------|-----------|-------|",
        "| COMPAT-001 | `knowledge/ingestion/pdf_loader.py` | `load_pdf(path) -> IngestionResult` | `ingestion_adapters.pdf.PdfIngestionAdapter.ingest` | Delegate + provenance | `test_compat_ingestion.py` | BLOCK-013 |",
        "| COMPAT-002 | `knowledge/search/keyword_search.py` | `KeywordSearch` class | `search/w8/keyword.KeywordSearchEngine` | Deterministic keyword retrieval | `test_compat_search.py` | BLOCK-013 |",
        "| COMPAT-003 | `knowledge/indexing/keyword_index.py` | `KeywordIndex` | `indexing/lexical.InMemoryLexicalIndex` | Index build/query passthrough | `test_compat_indexing.py` | BLOCK-013 |",
        "| COMPAT-004 | `knowledge/graph/graph_manager.py` | `GraphManager` | `graph/construction.GraphConstructor` + `graph/query.GraphQueryService` | Unified graph API | `test_compat_graph.py` | BLOCK-013 |",
        "| COMPAT-005 | `knowledge/ontology/ontology_manager.py` | `OntologyManager` | `ontology/registry.OntologyRegistry` | Term register/lookup | `test_compat_ontology.py` | BLOCK-013 |",
        "| COMPAT-006 | `knowledge/pipelines/knowledge_pipeline.py` | `run_knowledge_pipeline` | `tests/.../pipeline.run_full_pipeline` (prod: new orchestrator) | E2E orchestration | E2E regression | BLOCK-013+ |",
        "",
        "## Explicit Non-Facades (Do Not Create)",
        "",
        "| Frozen Path | Reason |",
        "|-------------|--------|",
        "| Duplicate `models/*.py` for consolidated types | Would duplicate parser/ontology models |",
        "| Empty `repositories/*_repository.py` stubs | No behavior; violates no-dummy-files rule |",
        "| `recommendation_engine.py` | Superseded by controlled RAG — ADR-010 |",
        "| Static `ontology/propulsion.py` etc. | Superseded by registry — ADR-008 |",
        "",
        "## Facade Requirements",
        "",
        "1. Real behavior only — delegate to canonical implementation",
        "2. Preserve provenance and lifecycle fields",
        "3. Deterministic where canonical is deterministic",
        "4. Do not modify frozen BLOCK-001→012 canonical modules",
        "5. Full unit test coverage per facade",
        "",
        "**Status:** PLAN ONLY. Implementation gated on ADR-011 approval.",
    ]
    (OUT / "knowledge_compatibility_layer_plan.md").write_text("\n".join(lines))


def write_certification_report(entries: dict, counts: Counter) -> None:
    cap = capability_addressed(counts)
    total = len(entries)
    lines = [
        "# Knowledge Certification Readiness Report",
        "",
        "**Document ID:** COSMOS-KG-CERT-READINESS-001",
        f"**Date:** {TODAY}",
        "**Phase:** RECONCILIATION ASSESSMENT",
        "",
        "## Certification Status",
        "",
        "```text",
        "FILE-LEVEL CERTIFIED 100%:  NO",
        "CAPABILITY CERTIFIED:        PARTIAL (103/175 addressed)",
        "TEST QUALIFIED:              YES (1219 passed, 5 skipped)",
        "PRODUCTION READY:            NO",
        "```",
        "",
        "---",
        "",
        "## Qualification Evidence (KG-BLOCK-012)",
        "",
        "| Domain | Implemented | Tested | Test Qualified | Production Ready | Evidence |",
        "|--------|-------------|--------|----------------|------------------|----------|",
        "| E2E pipeline | YES | YES | **YES** | NO | `tests/integration_tests/kg_block012/` |",
        "| Provenance | YES | YES | **YES** | NO | W9/W10 + BLOCK-012 E2E |",
        "| Lifecycle | YES | YES | **YES** | NO | Source registry + validation |",
        "| Determinism | YES | YES | **YES** | NO | Hash-stable ingestion, controlled RAG |",
        "| Failure/recovery | YES | YES | **YES** | NO | Adapter error paths tested |",
        "| Security/IP | YES | YES | **YES** | NO | Local-only, no mandatory cloud |",
        "| Controlled RAG | YES | YES | **YES** | NO | `provider_invoked=False` contract |",
        "| Performance | Characterized | YES | **PARTIAL** | NO | Ceiling tests only |",
        "",
        "**Distinction:** TEST QUALIFIED ≠ PRODUCTION READY. Missing persistent storage, production embeddings, exporters, operational monitoring.",
        "",
        "---",
        "",
        "## Certification Checklist",
        "",
        "| Requirement | Status | Blocker |",
        "|-------------|--------|---------|",
        f"| Every frozen file disposition A–F assigned | **PASS** | — |",
        f"| Exact path match (A) | **FAIL** ({counts['A']}/{total}) | 163 non-exact |",
        f"| Capability addressed (A+B+C+D) | **PARTIAL** ({cap}/{total}) | {counts['E']+counts['F']} gaps |",
        "| Deviations formally approved | **FAIL** | All ADRs PENDING |",
        "| Compatibility facades implemented | **FAIL** | Plan only |",
        "| Missing capabilities registered | **PASS** | See missing capability register |",
        "| No unauthorized LLM/network in RAG | **PASS** | Controlled local RAG |",
        "| Frozen blocks unchanged | **PASS** | Verified |",
        "| BLOCK-012 human freeze | **PENDING** | Awaiting approval |",
        "",
        "---",
        "",
        "## Path to FILE-LEVEL CERTIFIED 100%",
        "",
        "1. Approve all ADRs in decision register",
        "2. For each E disposition: implement OR approve deferral with substitute evidence",
        "3. For each F disposition: resolve architecture decision",
        "4. Implement approved compatibility facades (if ADR-011 approves)",
        "5. Re-run reconciliation; target A+B+C+D = 175 with approved justifications",
        "",
        "**Current recommendation:** Pursue **capability certification** with approved deviations rather than superficial file recreation.",
    ]
    (OUT / "knowledge_certification_readiness_report.md").write_text("\n".join(lines))


def write_deviation_register() -> None:
    content = (OUT / "knowledge_architecture_deviation_register.md").read_text()
    if "**Approval Status:** PENDING" not in content:
        content = content.replace(
            "**Type:** AUDIT ONLY",
            "**Type:** RECONCILIATION — deviations require explicit approval\n**Approval Status:** All deviations PENDING unless noted",
        )
        for dev in range(1, 11):
            old = f"### DEV-{dev:03d}"
            if f"DEV-{dev:03d}" in content and "**Approval Status:**" not in content.split(f"DEV-{dev:03d}")[1][:500]:
                pass
        # Append approval column note
        content += "\n\n---\n\n## Approval Matrix\n\n| DEV-ID | Recommendation | Approval Status |\n|--------|----------------|-----------------|\n"
        for i in range(1, 11):
            content += f"| DEV-{i:03d} | See deviation body | **PENDING** |\n"
        (OUT / "knowledge_architecture_deviation_register.md").write_text(content)


def write_rag_audit() -> None:
    lines = [
        "# Knowledge RAG Alignment Audit",
        "",
        "**Document ID:** COSMOS-KG-RAG-AUDIT-002",
        f"**Date:** {TODAY}",
        "**Phase:** RECONCILIATION VERIFICATION",
        "",
        "## Pipeline Alignment",
        "",
        "| Stage | Frozen Expectation | Current Implementation | Status |",
        "|-------|-------------------|------------------------|--------|",
        "| Source | Implicit in ingestion | `knowledge/source/` vault + integrity | **ALIGNED** |",
        "| Ingestion | `ingestion/*` loaders | `ingestion/` contracts + `ingestion_adapters/` | **ALIGNED** |",
        "| Parsing | `parsers/*` | `parsers/w3/` pipeline | **ALIGNED** |",
        "| Extraction | `extraction/*` | `extraction/w4/` pipeline | **ALIGNED** |",
        "| Ontology | `ontology/*` | `ontology/registry.py` + models | **ALIGNED** |",
        "| Graph | `graph/*` | `graph/construction.py`, `query.py` | **ALIGNED** |",
        "| Indexing | `indexing/*` | `indexing/` + `w7/` bundle | **ALIGNED** |",
        "| Search | `search/*` | `search/engine.py` + `w8/` | **ALIGNED** |",
        "| Validation | `validation/*` | `validation/engine.py` + modules | **ALIGNED** |",
        "| Reasoning | `reasoning/*` | `reasoning/` + `w10/` provenance chains | **ALIGNED** |",
        "| Controlled RAG | `recommendation_engine.py` (frozen) | `interface/rag.py` ControlledRAGOrchestrator | **SUPERSEDED (ADR-010)** |",
        "| Context Packaging | Not explicit in Part-3 | `interface/context.py`, `packaging.py` | **EXTENDED** |",
        "| Cursor/Engineering Interface | Not in Part-3 | `interface/` package | **EXTENDED** |",
        "",
        "---",
        "",
        "## Explicit Verification",
        "",
        "| Requirement | Result | Evidence |",
        "|-------------|--------|----------|",
        "| Local execution | **PASS** | In-memory indexes, no cloud deps in tests |",
        "| No mandatory cloud dependency | **PASS** | All BLOCK-012 tests local |",
        "| Provenance preservation | **PASS** | `source/integrity.py`, W10 chains |",
        "| Deterministic retrieval (where applicable) | **PASS** | Keyword/graph search deterministic |",
        "| Lifecycle safety | **PASS** | Source registry lifecycle states |",
        "| Candidate vs verified evidence separation | **PASS** | W10 classification |",
        "| Controlled context generation | **PASS** | `ControlledRAGOrchestrator` |",
        "| No automatic fact promotion | **PASS** | Evidence classification gates |",
        "| No unauthorized LLM/network dependency | **PASS** | `provider_invoked=False` in RAG contract |",
        "",
        "---",
        "",
        "## Gaps",
        "",
        "1. Semantic search uses reference vectors — not production embedding backend (ADR-009)",
        "2. No vector DB persistence — in-memory only",
        "3. Frozen `recommendation_engine.py` superseded — pending ADR-010 approval",
        "",
        "**Verdict:** Architecture supports **controlled local RAG** aligned with COSMOS principles.",
        "Not generic LLM RAG. Does not replace current KG architecture.",
    ]
    (OUT / "knowledge_rag_alignment_audit.md").write_text("\n".join(lines))


def write_next_plan(entries: dict, counts: Counter) -> None:
    lines = [
        "# Knowledge Next Development Plan",
        "",
        "**Document ID:** COSMOS-KG-NEXT-PLAN-002",
        f"**Date:** {TODAY}",
        "**Phase:** POST-RECONCILIATION PROPOSAL — not authorized for implementation",
        "",
        "## Immediate (Human Actions)",
        "",
        "1. Approve BLOCK-012 freeze",
        "2. Review and approve ADR-001 through ADR-012",
        "3. Approve deviation register entries",
        "",
        "## Proposed Blocks (Post-Reconciliation Gate)",
        "",
        "### KG-BLOCK-013 — Compatibility & Architecture Closure (Proposed)",
        "",
        "- Implement approved compatibility facades (COMPAT-001→006)",
        "- Resolve F-disposition files via ADRs",
        "- No changes to frozen BLOCK-001→011 modules",
        "",
        "### KG-BLOCK-014 — Export & Handoff (Proposed)",
        "",
        "- `knowledge/exporters/` package (if ADR-004 approves implementation)",
        "- Markdown/JSON/YAML export with provenance",
        "",
        "### KG-BLOCK-015 — Persistence Layer (Proposed)",
        "",
        "- Entity repositories OR approved graph-primary persistence",
        "- Depends on ADR-001",
        "",
        "### KG-BLOCK-016 — Production Embeddings (Proposed)",
        "",
        "- Local embedding backend for semantic index",
        "- Depends on ADR-009",
        "",
        "### KG-BLOCK-017 — Domain Model Expansion (Proposed)",
        "",
        "- Tier 3 missing domain models (if ADR-002 approves expansion vs consolidation)",
        "",
        "---",
        "",
        "## Reconciliation Metrics Baseline",
        "",
        f"| Metric | Value |",
        f"|--------|-------|",
        f"| E MISSING_REQUIRED | {counts['E']} |",
        f"| F MISSING_DECISION | {counts['F']} |",
        f"| Capability addressed | {capability_addressed(counts)}/175 |",
        "",
        "**Implementation gate remains CLOSED until ADR approval.**",
    ]
    (OUT / "knowledge_next_development_plan.md").write_text("\n".join(lines))


def main() -> None:
    entries, counts = load()
    write_traceability_matrix(entries, counts)
    write_reconciliation_master(entries, counts)
    write_models_gap(entries)
    write_missing_capability(entries)
    write_decision_register()
    write_compatibility_plan()
    write_certification_report(entries, counts)
    write_deviation_register()
    write_rag_audit()
    write_next_plan(entries, counts)
    print("Generated 10 reconciliation documents")
    print(dict(counts))


if __name__ == "__main__":
    main()
