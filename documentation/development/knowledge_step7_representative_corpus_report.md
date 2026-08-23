# Step 7 — Representative Engineering Corpus Report

**Document ID:** `COSMOS-STEP7-REPRESENTATIVE-CORPUS-001`  
**Date:** 2026-08-23  
**Manifest version:** `1.0.0`

---

## 1. Corpus Identity

| Field | Value |
|-------|-------|
| Location | `tests/fixtures/knowledge/representative_corpus.py` |
| Document count | 15 |
| Query count | 8 (labeled relevance) |
| License | COSMOS test fixture — synthetic engineering text |
| Proprietary content | **NONE** committed |
| Source type | Locally authored markdown summaries |

---

## 2. Domain Coverage

| Domain | Document IDs |
|--------|--------------|
| Propulsion | DOC-PROP-LOX, DOC-PROP-LH2, DOC-PROP-RP1 |
| Thermodynamics | DOC-THERMO-ENTROPY, DOC-THERMO-CYCLES |
| Fluid mechanics | DOC-FLUID-REYNOLDS, DOC-FLUID-MACH |
| Combustion | DOC-COMB-INSTABILITY |
| Heat transfer | DOC-HEAT-CONDUCTION, DOC-HEAT-CONVECTION, DOC-HEAT-RADIATION |
| Materials | DOC-MAT-COMPOSITE |
| Structures | DOC-STRUCT-STRESS |
| Aerospace systems | DOC-AERO-CONTROL |
| Equations | DOC-EQ-IMPULSE |

---

## 3. Benchmark Configuration

```text
evaluation_k:              5
backends_compared:         deterministic, neural
semantic_evaluator:        knowledge/production/semantic_retrieval_evaluation.py
scale_corpus_generator:    knowledge/production/scale_benchmark.generate_scale_corpus
```

---

## 4. Classification

Representative corpus semantic evaluation: **VERIFIED**  
Production engineering corpus qualification: **NOT VERIFIED**
