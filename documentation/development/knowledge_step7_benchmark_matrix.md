# Step 7 — Benchmark Matrix

| Operation | Cold | Warm | Single-Doc | Multi-Doc | Measured | Scale |
|-----------|------|------|------------|-----------|----------|-------|
| Ingestion end-to-end | ✅ | — | ✅ | ✅ | ✅ | 1–5 docs |
| Parsing/extraction | — | — | ✅* | ✅* | ⚠️ bundled | 1–5 docs |
| Indexing | — | — | ✅* | ✅* | ⚠️ bundled | 1–5 docs |
| Query | ✅ | ✅ | ✅ | ✅ | ✅ | 1–5 docs |
| Keyword retrieval | — | — | ✅* | ✅* | ⚠️ via hybrid | 1–5 docs |
| Vector retrieval | — | — | ✅* | ✅* | ⚠️ via hybrid | 1–5 docs |
| Graph retrieval | — | — | ✅* | ✅* | ⚠️ via hybrid | 1–5 docs |
| Hybrid retrieval | — | ✅ | ✅ | ✅ | ✅ | 1–5 docs |
| End-to-end RAG | ✅ | ✅ | ✅ | ✅ | ✅ | 1–5 docs |
| Persistence load/save | ✅ | — | ✅ | ✅ | ✅ | 1–5 docs |
| Recovery/rebuild | ✅ | — | ✅ | ✅ | ✅ | 1–5 docs |
| Memory usage | ✅ | — | ✅ | ✅ | ✅ | 1–5 docs |
| Storage footprint | — | — | ✅ | ✅ | ✅ | 1–5 docs |

\*Included in end-to-end ingestion timing, not isolated.

## Unverified Scale

| Operation | Target Scale | Status |
|-----------|--------------|--------|
| All operations | 100+ documents | NOT VERIFIED |
| All operations | Sustained query load | NOT VERIFIED |
| All operations | GB-scale storage | NOT VERIFIED |
