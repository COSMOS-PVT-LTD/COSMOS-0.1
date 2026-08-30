# Knowledge Integration — Test Plan

**ID:** KI-INTEG-2026-08-30

## Scope

Verify GUI→API→Knowledge→RAG→Evidence chain for Envelope B without modifying frozen KG-BLOCK modules.

## Test modes

| Mode | Description |
|------|-------------|
| API-EQUIVALENT | Desktop shell HTTP proxy reproduces maharshi.js workflow |
| Unit/Integration | Existing knowledge + new qualification tests |

## Test matrix

| ID | Scenario | Method | Evidence |
|----|----------|--------|----------|
| KI-T01 | Unauthenticated API blocked | Integration | HTTP 401 |
| KI-T02 | Login→ingest→graph→chat→evidence | Integration | KI-T02 payload assertions |
| KI-T03 | Persistence after workspace reload | Integration | vault.verify + search |
| KI-T04 | Delete→re-ingest | Integration | graph node removal |
| KI-T05 | VIEWER cannot ingest | Integration | HTTP 403 |
| KI-T06 | maharshi.js endpoint contract | Integration | 200 on health/sources/jobs/review/graph |
| KI-T07 | No mission-specific fabrication | Integration | empty document_ids |
| KI-U* | Knowledge unit suite | pytest | 1054 passed |
| KI-P* | Production/offline/neural | pytest | step7 tests |

## Documents

- Primary: `knowledge/workspace/corpus.py` `cooling_markdown_bytes()` (regenerative cooling)
- Secondary: `reynolds_pdf_bytes()` in approve/review tests (existing)

## Out of scope (Envelope B)

- 50+ document scale
- 8-way concurrency
- Mandatory cloud providers
- Browser Playwright automation (deferred)

## Exit criteria

- All new integration tests PASS
- Full regression 0 failures
- No frozen file modifications
- Evidence artifacts committed under `documentation/development/`
