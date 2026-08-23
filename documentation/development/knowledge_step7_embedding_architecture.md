# Step 7 — Embedding Architecture

## Model Identity

```python
EmbeddingModelIdentity(
    model_id="cosmos-local-deterministic-v1",
    dimensions=384,
    normalization="l2",
    provider="local-deterministic",
)
```

## Backend: `DeterministicLocalEmbeddingBackend`

| Property | Value |
|----------|-------|
| Network required | **No** |
| Model download | **No** |
| Deterministic | **Yes** (SHA-256 seed → pseudo-vector) |
| Dimensions | 384 |
| Normalization | L2 unit vector |

## Algorithm (Summary)

1. Hash input text with SHA-256
2. Expand hash bytes into 384 float components via deterministic PRNG seeding
3. L2-normalize resulting vector

## Rationale

- Enables **fully offline** production RAG qualification without external dependencies
- Guarantees **reproducible** embeddings across runs and machines
- Provides semantic-path plumbing for W7 index bundles

## Trade-offs

| Advantage | Limitation |
|-----------|------------|
| Zero latency for model load | Not semantically meaningful (not neural) |
| No IP/licensing concerns for model weights | Retrieval quality ceiling lower than transformer embeddings |
| Perfect for CI/integration tests | Not recommended as final production embedding strategy |

## Future Path

Replace `DeterministicLocalEmbeddingBackend` with a local ONNX/sentence-transformers backend behind the same `EmbeddingModelIdentity` contract, with explicit model governance (Step 5 disposition) and offline bundle packaging.

## Offline Guard Integration

`OfflineExecutionGuard` tracks `provider_invoked=False`. The deterministic backend never sets provider invocation — preserving certification invariants.
