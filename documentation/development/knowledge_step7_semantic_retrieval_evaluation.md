# Step 7 — Semantic Retrieval Evaluation

**Document ID:** `COSMOS-STEP7-SEMANTIC-RETRIEVAL-EVAL-001`  
**Date:** 2026-08-23  
**Data source:** `knowledge_step7_final_semantic_evaluation_data.json`  
**Corpus:** 15 engineering documents, 8 labeled queries (`tests/fixtures/knowledge/representative_corpus.py`)  
**K:** 5

---

## 1. Measured Results

| Backend | Recall@5 | Precision@5 | MRR | nDCG@5 | Hit Rate | Mean Query Latency |
|---------|----------|-------------|-----|--------|----------|-------------------|
| Deterministic v1 | 0.417 | 0.125 | 0.292 | 0.303 | 0.500 | 0.008 ms |
| **Neural v1** | **0.875** | **0.275** | **0.813** | **0.800** | **0.875** | 5.336 ms |

---

## 2. Interpretation

Neural embeddings provide **material improvement** on terminology variation, synonym, and concept-to-document queries where deterministic hashing lacks semantic structure.

Examples where neural outperforms deterministic:

- `Q-LOX-SYN` — "liquid oxygen oxidizer bipropellant" → `DOC-PROP-LOX`
- `Q-HEAT-TRANSFER` — thermal cooling concept → heat transfer documents
- `Q-CHAMBER-LEX` — combustion instability vs. chamber pressure

Deterministic v1 remains faster and gate-qualified for Envelope A fixture workloads.

---

## 3. Query Coverage

Domains represented in evaluation set: propulsion, thermodynamics, fluids, combustion, heat transfer, structures, aerospace control, equations/abbreviations.

---

## 4. Classification

| Result | Status |
|--------|--------|
| Neural semantic retrieval quality | **VERIFIED** on representative corpus |
| Production corpus qualification | **NOT VERIFIED** — representative corpus only |
| Default qualification path metrics | Deterministic v1 (Envelope A) unchanged |
