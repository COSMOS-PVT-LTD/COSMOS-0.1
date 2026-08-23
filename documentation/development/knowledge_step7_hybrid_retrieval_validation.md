# Step 7 — Hybrid Retrieval Validation

**Document ID:** `COSMOS-STEP7-HYBRID-RETRIEVAL-VALIDATION-001`  
**Date:** 2026-08-23

---

## 1. Architecture Validated

```text
Keyword (lexical) + Neural semantic vectors + Graph adjacency
        ↓
HybridSearchEngine fusion
        ↓
Lifecycle/provenance filtering
        ↓
ControlledRAGOrchestrator
```

Preserved controls:

- `provider_invoked = False` on default path
- Document-scoped RAG via `allowed_document_ids`
- Vector dimension validation on load
- Model fingerprint + configuration hash mismatch detection
- Stale index detection via `source_digest`

---

## 2. Test Evidence

| Test | Result |
|------|--------|
| `test_neural_pipeline_ingest_query_offline` | PASS — neural ingest + query offline |
| `test_hybrid_retrieval_uses_local_embedding_backend` | PASS — semantic mode uses local backend |
| `test_step7_production_pipeline` (existing) | PASS — deterministic hybrid path |
| `test_step7_multi_document_ingestion` (existing) | PASS — graph merge + hybrid |

---

## 3. Retrieval Mode Behavior

| Mode | Query embedding | Engine |
|------|-----------------|--------|
| HYBRID | HybridSearchEngine default | Lexical + graph + vector fusion |
| SEMANTIC | `embedding_backend.embed_query()` | SemanticVectorSearchEngine |

---

## 4. Stability Assessment

| Check | Result |
|-------|--------|
| Deterministic repeat queries | Stable — warm/cold within ~2% at 100-doc scale |
| Neural index rebuild after ingest | Stable — configuration hash persisted |
| Model mismatch on reload | **SchemaMismatchError** raised (verified) |

**Classification:** Hybrid retrieval with neural backend is **VERIFIED** at fixture/representative scale. Production-scale hybrid stability is **PARTIALLY VERIFIED** (≤100 docs) and **CHARACTERIZED** (250–500 docs).
