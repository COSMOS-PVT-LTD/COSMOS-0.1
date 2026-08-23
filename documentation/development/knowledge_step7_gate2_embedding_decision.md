# Step 7 Gate 2 — Production Embedding Backend Decision

**Date:** 2026-08-23  
**Classification:** APPROVED WITH CONDITIONS

## Current Backend

| Attribute | Value |
|-----------|-------|
| Model ID | `cosmos-local-deterministic-v1` |
| Version | `1.0.0` |
| Provider | `local-deterministic` |
| Dimensions | Configurable (default 8 in pipeline) |
| Network | **Not required** |
| Licensing | N/A (no external model weights) |
| Reproducibility | **Bitwise deterministic** |
| CPU/GPU | CPU only |

## Evaluation Matrix

| Criterion | Deterministic v1 | Neural Local (e.g. ONNX) |
|-----------|------------------|--------------------------|
| Offline execution | ✅ | ✅ (if bundled) |
| Reproducibility | ✅ Bitwise | ⚠️ Envelope-based |
| Semantic quality | ❌ Low | ✅ High |
| IP/licensing risk | ✅ None | ⚠️ Model-dependent |
| CI qualification | ✅ | ⚠️ Artifact management needed |
| Migration/re-index | Trivial | Requires re-embed + bundle rebuild |

## Decision

```text
APPROVED WITH CONDITIONS — deterministic backend for qualification envelope
```

### Approved for Qualification

- `DeterministicLocalEmbeddingBackend` is approved for **controlled production qualification** at fixture scale
- Suitable for: CI, integration qualification, offline verification, plumbing validation

### Conditions (Human Gate 2)

1. **Neural backend selection** remains a **HUMAN DECISION** before production deployment with semantic retrieval requirements
2. Qualification reports must **not claim** semantic embedding quality with deterministic backend
3. Any neural backend must: execute locally, pin model version, document reproducibility envelope, require re-index on model change

### Not Fabricated

No neural model was downloaded or invoked. No cloud embedding API was introduced.

## Migration Path

When a neural backend is selected:

1. Create ADR for model selection
2. Implement behind `EmbeddingModelIdentity` contract
3. Bump index bundle format or embedding fingerprint
4. Execute full re-index
5. Re-run qualification benchmarks
