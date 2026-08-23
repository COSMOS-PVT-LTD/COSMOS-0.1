# COSMOS Step 5 — Model Decision Register

**Document ID:** `COSMOS-STEP5-MODEL-DECISION-REGISTER-001`  
**Date:** 2026-08-23  
**Baseline SHA:** `32dd3170440342ade8d879239b40707465553ad4`  
**Status:** READY FOR HUMAN REVIEW

---

## Register Summary

| Category | Count | Models |
|---|---|---|
| **Explicitly deferred (M3)** | 5 | appendix, glossary, boundary_condition, correlation, design_rule |
| **Consolidated (M2)** | 10 | section, chapter, assumption, experiment, failure_mode, manufacturing_process, physical_law, process, property, simulation |
| **Superseded (M4)** | 0 | — |
| **ADR required (M5)** | 0 | *(within 15-model set)* |
| **Genuine capability gaps (M6)** | **0** | — |
| **Legacy / non-essential (M7)** | 0 | — |

---

## Models Explicitly Deferred (M3)

| Model | Frozen Path | Rationale | Blocked By | Revisit Trigger |
|---|---|---|---|---|
| Appendix | `knowledge/models/appendix.py` | Generic `DocumentSection` sufficient for current parsing; appendix-specific semantics not authorized | `appendix_parser.py` (MCAP-049) | Human authorization for KG-BLOCK-014+ |
| Glossary | `knowledge/models/glossary.py` | Ontology terms cover partial definitional need; no glossary parser | `glossary_parser.py` (MCAP-050) | Glossary parser ADR + block authorization |
| Boundary Condition | `knowledge/models/boundary_condition.py` | CFD/FEA domain not in authorized capability | `boundary_condition_extractor.py` (MCAP-010) | Simulation domain pack authorization |
| Correlation | `knowledge/models/correlation.py` | Overlaps empirical_relation (F); no extractor | `empirical_relation.py` ADR + `correlation_extractor.py` | ADR closure then future block |
| Design Rule | `knowledge/models/design_rule.py` | No design rule extraction in authorized pipeline | `design_rule_extractor.py` (MCAP-012) | Domain extraction block authorization |

**Action for all M3:** DO NOT IMPLEMENT until separate human authorization and dependency closure.

---

## Models Consolidated (M2)

| Model | Frozen Path | Consolidated Into | Justification |
|---|---|---|---|
| Section | `knowledge/models/section.py` | `DocumentSection` (`parsers/models.py`) | W3 parse artifact, not domain entity (ADR-003) |
| Chapter | `knowledge/models/chapter.py` | `DocumentSection` hierarchy | Top-level sections = chapters |
| Assumption | `knowledge/models/assumption.py` | `EngineeringDomain.assumptions` + graph CLAIM | ID-reference pattern; no standalone model needed |
| Experiment | `knowledge/models/experiment.py` | `ExtractedEntityKind.EXPERIMENT` | Extraction + graph candidate sufficient |
| Failure Mode | `knowledge/models/failure_mode.py` | `Subsystem.failure_mode_ids` | ID-reference pattern per ADR-001 graph-primary |
| Manufacturing Process | `knowledge/models/manufacturing_process.py` | `ExtractedEntityKind.PROCESS` | Process kind covers manufacturing |
| Physical Law | `knowledge/models/physical_law.py` | `EngineeringDomain.physical_laws` | ID-reference pattern |
| Process | `knowledge/models/process.py` | `ExtractedEntityKind.PROCESS` | Extraction + graph sufficient |
| Property | `knowledge/models/property.py` | `Material` + `Quantity` | Duplication prohibition — properties embedded in Material |
| Simulation | `knowledge/models/simulation.py` | `Subsystem.simulation_case_ids` + `Quantity` | ID-reference pattern |

**Action for all M2:** DO NOT IMPLEMENT — document consolidation only.

---

## Models Superseded (M4)

None within the 15-model audit set.

Related superseded architecture (context only):

| Frozen Artifact | Superseded By | ADR |
|---|---|---|
| 15 `repositories/*_repository.py` | Graph-primary `GraphStore` | ADR-001 |
| 14 static `ontology/*.py` domain files | Dynamic `OntologyRegistry` | ADR-008 |
| Recommendation engine | Controlled RAG (`provider_invoked=False`) | ADR-010 |

---

## Models Requiring ADR (M5)

**None within the 15-model E set.**

### Related F-Tier Items (Outside 15-Model Set)

| Model | Frozen Path | ADR Topic | Status | Step 5 Action |
|---|---|---|---|---|
| Empirical Relation | `knowledge/models/empirical_relation.py` | Relation to correlation/physical_law models | **PENDING** (F) | Do not implement; await ADR |
| Sentence | `knowledge/models/sentence.py` | Sentence vs paragraph-only W3 parsing | **PENDING** (F) | Do not implement; await ADR |

These are tracked in `knowledge_missing_capability_register.md` as MCAP-038 and MCAP-047.

---

## Models Proposed as Genuine Capability Gaps (M6)

```text
NONE
```

No M6 items identified. Evidence standard (Step 5 §9) not met for any of the 15 models:

- No active runtime consumer requires the missing file
- No failing contract exists
- No demonstrated loss of information in authorized pipeline
- BLOCK-012 + Step 4 compatibility audits pass without these models

```text
M6 ITEMS ARE NOT AUTHORIZED FOR IMPLEMENTATION.
SEPARATE HUMAN AUTHORIZATION NOT REQUIRED (no M6 items exist).
```

---

## Prohibited Recreation Register

The following models are **explicitly prohibited** from file-level recreation:

| # | Model | Reason |
|---|---|---|
| 1–15 | All 15 E-disposition models | Audit complete; no capability gap |
| — | `empirical_relation.py` | ADR pending |
| — | `sentence.py` | ADR pending |

**Prohibition includes:** empty shells, type aliases masquerading as models, placeholder classes, and wrappers created solely to improve file-level match percentage.

---

## Decision Gate Records

| Decision ID | Date | Decision | Authority |
|---|---|---|---|
| STEP5-D-001 | 2026-08-23 | All 15 missing models: DEFER or CONSOLIDATE — no implementation | Step 5 audit |
| STEP5-D-002 | 2026-08-23 | Zero M6 genuine gaps — no implementation proposals required | Step 5 audit |
| STEP5-D-003 | 2026-08-23 | KG-BLOCK-014+ remains NOT AUTHORIZED | Preserved from Phase E |

---

## Human Review Checklist

- [ ] Technical owner confirms M2 consolidation map
- [ ] Technical owner confirms M3 deferral list
- [ ] Technical owner acknowledges F-tier ADR items (empirical_relation, sentence)
- [ ] Technical owner authorizes or rejects any future M6 proposals (none pending)
- [ ] Certification claims remain accurate (no production qualification inflation)

---

## Next Authorized Steps (Not Automatic)

1. Human review and approval of this register
2. ADR closure for F-tier items (if desired)
3. Separate authorization for KG-BLOCK-014+ (if desired)
4. Individual model implementation proposals (only if M6 evidence emerges)

**STOP after human review. Do not auto-implement.**
