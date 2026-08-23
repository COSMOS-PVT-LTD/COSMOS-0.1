# Knowledge Evolution Governance Plan

**Document ID:** COSMOS-KG-EVOL-GOV-PLAN-001  
**Date:** 2026-08-23  
**Version:** 1.0  
**Status:** PENDING TECHNICAL OWNER APPROVAL  
**Phase:** GOVERNANCE ONLY — no implementation

---

## 1. Executive Decision

**DO NOT RESTART THE KNOWLEDGE FOUNDATION.**

The COSMOS Knowledge Foundation will evolve through:

1. **Governed dispositions** for all 175 frozen architectural files (COMPLETE — L1 100%)
2. **Human-approved ADRs** for decision-required items
3. **Thin compatibility facades** where frozen API boundaries matter
4. **Selective capability closure** for genuine gaps only
5. **Preservation** of KG-001→051 modularity, provenance, determinism, and local controlled RAG

The target is **capability + contract + traceability + verification**, not **175 matching filenames**.

---

## 2. Current Baseline

| Metric | Value |
|--------|-------|
| Current `knowledge/**/*.py` | 148 |
| Frozen architecture files | 175 |
| Exact path match | 12 (6.9%) |
| Capability addressed (A+B+C+D) | 103 (58.9%) |
| Missing required (E) | 67 |
| Decision required (F) | 5 |
| Extra justified (G) | 100 |
| Extra review required (H) | 36 |
| Regression | 1219 passed, 5 skipped |
| BLOCK-001→011 | FROZEN |
| BLOCK-012 | **FROZEN** — TEST-QUALIFIED / INTEGRATION-QUALIFIED / NOT PRODUCTION-QUALIFIED |
| Production ready | NO |

**Source:** `knowledge_evolution_baseline_audit.md`

---

## 3. Frozen Architecture Relationship

| Role | Document |
|------|----------|
| Architectural reference | `documentation/COSMOS_0.1_FREEZED.md` Part 3 |
| File inventory authority | 175 `.py` files under `knowledge/` |
| Disposition authority | `kg_reconciliation_registry.json` |

**Principle:** Frozen tree defines *capabilities and contracts*. Current tree defines *implementation*. Neither silently overwrites the other.

---

## 4. KG-001→051 Relationship

| Aspect | Status |
|--------|--------|
| Workstreams W0→W11 | Implemented in evolved subpackages |
| KG-001→051 matrix | RECONCILED (prior approval record) |
| Block program | BLOCK-001→012 complete at test level |
| Implementation baseline | **KG-001→051 is authoritative for code** |
| File tree baseline | **Part-3 is authoritative for disposition** |

Evolution extends KG-001→051 — does not replace it.

---

## 5. File Reconciliation Summary

See `knowledge_file_level_architecture_reconciliation.md` and decision gate table DG-001→199.

**Level 1 (File Reconciliation):** 175/175 dispositioned = **100%**

---

## 6. Capability Gap Analysis (E + F → GAP Classification)

### GAP-1 — TRUE CAPABILITY GAP (implement after authorization)

| Item | Count | Proposed Block |
|------|-------|----------------|
| Exporters package | 7 | BLOCK-014 |
| Format loaders (epub, latex, image, ocr, markitdown) | 5 | BLOCK-013+ (prioritized) |
| `batch_loader.py` | 1 | BLOCK-013+ |
| `citation_validator.py` | 1 | BLOCK-013 |
| `ambiguity_detector.py` | 1 | BLOCK-013 |
| Glossary/appendix parsers + extractors | 4 | BLOCK-013+ |
| Domain models (11) | 11 | BLOCK-017 |

**Total GAP-1:** ~30 items (not all in BLOCK-013)

### GAP-2 — COMPATIBILITY GAP (thin facade)

| Item | Count | Facade IDs |
|------|-------|------------|
| Ingestion loaders at frozen paths | 4 | COMPAT-001 |
| Search modules at frozen paths | 5 | COMPAT-002 |
| Index modules at frozen paths | 3 | COMPAT-003 |
| Graph manager | 1 | COMPAT-004 |
| Ontology manager | 1 | COMPAT-005 |
| Knowledge pipeline orchestrator | 1 | COMPAT-006 |

**Total GAP-2:** 13 facade targets (BLOCK-013 Phase B)

### GAP-3 — ARCHITECTURAL CONSOLIDATION (do not recreate)

| Category | Count | Action |
|----------|-------|--------|
| C-disposition files | 48 | APPROVE consolidation |
| E extractors covered by W4 | 11 | CONSOLIDATE into W4 |
| E specialized indexes/search | 6 | CONSOLIDATE into W7/W8 facets |
| E structure models | 4 | CONSOLIDATE into W3 |
| H review-required canonical files | 36 | APPROVE as canonical |

**Total GAP-3:** 105 items — **no file recreation**

### GAP-4 — SUPERSEDED (do not recreate)

| Category | Count |
|----------|-------|
| D-disposition (ontology domains, recommender, logging) | 16 |
| F sentence model/parser | 2 |

**Total GAP-4:** 18 items

### GAP-5 — DECISION REQUIRED (ADR before action)

| File | ADR |
|------|-----|
| `concept_graph.py` | ADR-007 |
| `empirical_relation.py` | ADR-006 |
| `sentence.py` | ADR-005 |
| `sentence_parser.py` | ADR-005 |
| `text_utils.py` | Minor — implement if approved |

### GAP-6 — LEGACY / NON-ESSENTIAL (remove from architecture)

| Item | Count | Rationale |
|------|-------|-----------|
| Entity repositories (`repositories/*_repository.py`) | 14 | Graph-primary persistence; duplicate subsystem |
| `equation_reasoner.py` | 1 | Covered by W10 reasoner |
| `citation_graph.py` | 1 | Citation edges in main graph |

**Total GAP-6:** 16 items — **REMOVE FROM ARCHITECTURE** (not implement)

---

## 7. Compatibility Gap Analysis

See `knowledge_compatibility_layer_plan.md`.

| Facade | Frozen Path | Canonical | Priority |
|--------|-------------|-----------|----------|
| COMPAT-001 | `ingestion/*_loader.py` | `ingestion_adapters/*` | P1 |
| COMPAT-002 | `search/*_search.py`, `search_engine.py` | `search/w8/*`, `search/engine.py` | P1 |
| COMPAT-003 | `indexing/*_index.py` | `indexing/lexical.py`, `semantic.py`, `w7/graph_index.py` | P1 |
| COMPAT-004 | `graph/graph_manager.py` | `graph/construction.py` + `query.py` | P1 |
| COMPAT-005 | `ontology/ontology_manager.py` | `ontology/registry.py` | P1 |
| COMPAT-006 | `pipelines/knowledge_pipeline.py` | Production orchestrator (test helper interim) | P2 |

**Facade rules:** thin, delegating, tested, non-authoritative, provenance-preserving.

---

## 8. Model Strategy

See `knowledge_model_architecture_decisions.md`.

```text
11 APPROVE (exact)
 8 CONSOLIDATE (no new files)
 2 SUPERSEDE/CONSOLIDATE (ADR-gated)
11 DEFER (BLOCK-017 domain expansion)
 4 CONSOLIDATE structure to W3
 0 blind file creation
```

---

## 9. ADR Strategy

| ADR | Topic | Gate For | Status |
|-----|-------|----------|--------|
| ADR-001 | Repository plural vs graph-primary | 14 entity repos | **APPROVED** (2026-08-23) |
| ADR-002 | Model consolidation vs expansion | 11 domain models | PENDING |
| ADR-003 | W3/W4/W7/W8/W10 subpackages | Structural evolution | **APPROVED** (2026-08-23) |
| ADR-004 | Exporters package | 7 exporter files | PENDING |
| ADR-005 | Sentence-level parsing | sentence.py, sentence_parser.py | PENDING |
| ADR-006 | Empirical relation | empirical_relation.py | PENDING |
| ADR-007 | Concept graph | concept_graph.py | PENDING |
| ADR-008 | Static ontology domains | 14 superseded domain files | **APPROVED** (2026-08-23) |
| ADR-009 | Semantic embeddings | Production RAG | PENDING |
| ADR-010 | Controlled RAG vs recommender | recommendation_engine.py | **APPROVED** (2026-08-23) |
| ADR-011 | Compatibility facades | 13 facade targets | **APPROVED** (2026-08-23) |
| ADR-012 | BLOCK-012 freeze | Integration qualification | **APPROVED** (2026-08-23) |

**Rule:** No ADR approval = no F-disposition implementation.

---

## 10. Deviation Strategy (DEV-001→010)

| DEV | Topic | Status |
|-----|-------|--------|
| DEV-001 | Repositories plural vs singular | **CLOSED** — ADR-001 |
| DEV-002 | Missing exporters | **OPEN** — defer BLOCK-014 |
| DEV-003 | Model consolidation | **OPEN** — ADR-002 pending |
| DEV-004 | W3/W4/W7/W8/W10/W11 subpackages | **CLOSED** — ADR-003 |
| DEV-005 | `knowledge/source/` extension | **ACCEPTED** |
| DEV-006 | `ingestion_adapters/` extension | **ACCEPTED** |
| DEV-007 | Static ontology domains superseded | **CLOSED** — ADR-008 |
| DEV-008 | Reference embeddings only | **OPEN** — ADR-009 pending |
| DEV-009 | Controlled RAG without LLM | **CLOSED** — ADR-010 |
| DEV-010 | `pdf_normalizer.py` untested | **OPEN** |

No deviation approved by code existence alone.

---

## 11. RAG Production Roadmap

| ID | Item | Classification |
|----|------|----------------|
| RAG-001 | Local embedding backend | **Required later** — ADR-009 |
| RAG-002 | Persistent vector index | **Required later** — BLOCK-016 |
| RAG-003 | Persistent graph/index state | **Required later** — BLOCK-015 |
| RAG-004 | Incremental indexing | **Required later** |
| RAG-005 | Document update invalidation | **Required later** |
| RAG-006 | Multi-document retrieval | **Partial** — hybrid search exists |
| RAG-007 | Source-aware retrieval filters | **Implemented** — W8 validation-aware |
| RAG-008 | Engineering-domain filters | **Partial** — ontology registry |
| RAG-009 | Provenance-aware context assembly | **Implemented** — W10/W11 |
| RAG-010 | Context-size budgeting | **Implemented** — interface/context.py |
| RAG-011 | Local inference provider interface | **Optional** — no mandatory LLM |
| RAG-012 | Optional local LLM integration | **Optional** — explicit config only |

**Preserve:** `provider_invoked=False` contract; no mandatory cloud/LLM.

---

## 12. Persistence Roadmap

| Phase | Scope | Block |
|-------|-------|-------|
| Current | In-memory graph store, indexes | — |
| Next | Source registry persistence (if needed) | BLOCK-015 |
| Later | Vector/graph durable storage | BLOCK-015/016 |
| Not planned | 14 entity-specific repositories | REMOVED per ADR-001 |

---

## 13. Embedding Roadmap

| Stage | Description |
|-------|-------------|
| Current | Reference vectors in `indexing/w7/vector.py` — test-qualified |
| Next | `EmbeddingProvider` interface with **local** default |
| Optional | External provider behind explicit configuration |
| Constraint | Core KG MUST operate without external provider |

---

## 14. Security / IP Strategy

All evolution work must preserve:

- No silent document transmission
- No mandatory cloud services
- No unauthorized API calls
- No execution of extracted content
- No mutation of source evidence
- No automatic candidate promotion
- Provenance chain integrity (release-blocking if broken)

---

## 15. Verification Strategy

| Level | Target | Current |
|-------|--------|---------|
| L1 File reconciliation | 100% | **100%** |
| L2 Capability certification | 100% | 58.9% + governed deferrals |
| L3 Contract certification | 100% | Partial — facades pending |
| L4 Test certification | 100% | Partial — exporter/repo gaps |
| L5 Production qualification | Controlled release | Not met |

**Requirements for new work:** unit + contract + integration + determinism + provenance tests; full regression mandatory.

---

## 16. Proposed KG-BLOCK-013 Scope

See `kg_block_013_candidate_scope.md`.

**Summary:** Governance/ADR closure → compatibility facades → selective capability gaps → verification → certification update.

**NOT in BLOCK-013 by default:** exporters, persistence, embeddings, domain model expansion.

---

## 17. Explicitly Deferred Work

| Item | Defer To | Reason |
|------|----------|--------|
| Exporters (7) | BLOCK-014 | No current consumer; engineering handoff |
| Domain models (11) | BLOCK-017 | ADR-002; W4/graph interim |
| Entity repositories (14) | REMOVED | ADR-001 graph-primary |
| Production embeddings | BLOCK-016 | ADR-009 |
| Persistent storage | BLOCK-015 | Infrastructure |
| Sentence infrastructure | ADR-005 decision | Not required by current pipeline |
| Static ontology modules | Never | Superseded by registry |

---

## 18. Risks

| Risk | Severity | Mitigation |
|------|----------|------------|
| Mechanical file recreation | HIGH | Governance gate; no-dummy-files rule |
| Duplicate models/state | HIGH | Model decision register |
| Frozen block regression | CRITICAL | No modification without defect + authorization |
| Facade logic duplication | MEDIUM | Delegate-only facades with tests |
| Premature production claim | HIGH | Distinguish TEST QUALIFIED vs PROD READY |
| ADR bypass | HIGH | Implementation gate closed |
| Second graph authority | MEDIUM | Single graph model — ADR-007 |
| Cloud/LLM dependency creep | HIGH | RAG roadmap constraints |

---

## 19. Acceptance Criteria (Governance Phase)

```text
[✓] 175/175 frozen files dispositioned
[✓] All deviations identified (DEV-001→010)
[✓] All decision-required items identified (F + ADRs)
[✓] True capability gaps classified (GAP-1)
[✓] Compatibility gaps classified (GAP-2)
[✓] Model strategy documented
[✓] RAG architecture preserved
[✓] KG-BLOCK-013 scope justified
[✓] No unnecessary recreation planned
[✓] Human BLOCK-012 freeze
[✓] KG-BLOCK-013 Phase A complete
[✓] Minimum ADR set closed (ADR-001, 003, 008, 010, 011 strategy, 012)
[ ] Human approval of decision gate table (full)
[ ] Human approval of remaining ADRs (002, 004–007, 009)
[ ] Explicit KG-BLOCK-013 implementation authorization
```

---

## Implementation Gate

```text
CLOSED — KG-BLOCK-013 PHASE A COMPLETE
PHASE B — READY (separate implementation authorization required)
PHASE C/D/E — NOT AUTHORIZED
```
