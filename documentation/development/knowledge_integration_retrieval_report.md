# Knowledge Integration — Retrieval Report

## Modes available (codebase)

| Mode | Module |
|------|--------|
| Keyword/lexical | `knowledge/search/keyword_search.py` |
| Semantic | `knowledge/search/semantic_search.py` |
| Hybrid | `knowledge/brain/hybrid.py` |
| Neural semantic | `knowledge/embeddings/neural_backend.py` + production pipeline |
| Graph | `knowledge/search/graph_search.py` |

## Qualification evidence

| Query type | Test | Result |
|------------|------|--------|
| Exact terminology | KI-T02 "regenerative cooling" | PASS — hits + chat evidence |
| Semantic paraphrase | KI-T02 alternate wording | PASS — evidence returned |
| Post-delete | KI-T04 | PASS — deleted source not in document_ids |
| Mission-specific (no upload) | KI-T07 | PASS — no fabricated mission ID in conclusion |

## Neural backend

Verified in unit tests (`test_step7_neural_embeddings.py`):
- `cosmos-local-neural-mini-v1`
- 64 dimensions, deterministic, local, offline
- `provider_invoked=False` in production pipeline tests

## Envelope

Retrieval qualification remains within Envelope B (≤25 docs). Scale benchmarks in prior Step-7 reports not re-run this session.
