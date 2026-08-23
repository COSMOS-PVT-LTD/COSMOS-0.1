# Step 7 — Neural Embedding Selection

**Document ID:** `COSMOS-STEP7-NEURAL-EMBEDDING-SELECTION-001`  
**Date:** 2026-08-23

---

## 1. Selection Summary

**Selected model:** `cosmos-local-neural-mini-v1`  
**Implementation:** `LocalNeuralEmbeddingBackend` — seeded MLP over engineering feature encoder  
**Provider:** `local-neural-mlp`  
**Version:** `1.0.0`  
**Dimension:** 64  
**Network required at runtime:** **NO**  
**Pinned configuration hash:** recorded in persisted index bundle via `EmbeddingService.metadata()`

**Fallback:** `cosmos-local-deterministic-v1` (Gate-2 closed qualification path)

---

## 2. Candidate Evaluation

| Candidate | Retrieval (Recall@5) | RAM | CPU | Latency (query) | License | Offline | Verdict |
|-----------|---------------------|-----|-----|-----------------|---------|---------|---------|
| Deterministic v1 | 0.417 | ~32 MB | trivial | 0.008 ms | COSMOS | YES | Qualification default |
| **cosmos-local-neural-mini-v1** | **0.875** | ~35 MB | feasible | 5.3 ms | COSMOS | YES | **SELECTED** |
| sentence-transformers/all-MiniLM-L6-v2 | not integrated | ~200+ MB | moderate | varies | Apache-2.0 | after download | **REJECTED** — adds heavyweight dependency, download provisioning |
| OpenAI text-embedding-3 | N/A | cloud | cloud | cloud | commercial | NO | **REJECTED** — violates local-first / `provider_invoked=False` |

Measured comparison source: `knowledge_step7_final_semantic_evaluation_data.json`

---

## 3. Engineering Suitability

| Criterion | Assessment |
|-----------|------------|
| Terminology variation / synonyms | Improved — hit rate 0.50 → 0.875 |
| Abbreviations (Isp, LOX, LH2) | Improved on representative queries |
| Engineering domains covered | Propulsion, thermo, fluids, combustion, heat, materials, structures, aerospace |
| Reproducibility | Seeded weights — identical vectors for fixed input |
| Indexing cost | ~144 ms/doc at 100-doc synthetic scale (deterministic pipeline overhead dominates) |
| Batch support | `embed_batch()` implemented |

---

## 4. Pinned Configuration

```text
model_id:                cosmos-local-neural-mini-v1
model_version:           1.0.0
feature_dimension:       512
hidden_dimension:        128
output_dimension:        64
weight_seed:             cosmos-local-neural-mini-v1@1.0.0
requires_network:        false
```

---

## 5. Recommendation

Deploy neural backend via `embedding_mode="neural"` for semantic retrieval characterization and Gate-6 evidence. **Default production qualification path remains deterministic v1 (Envelope A)** until human Gate-6 review authorizes neural qualification.
