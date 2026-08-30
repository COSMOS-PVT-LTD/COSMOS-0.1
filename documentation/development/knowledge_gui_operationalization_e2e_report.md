# Knowledge GUI Operationalization — E2E Report

**Mode:** API-EQUIVALENT (desktop shell proxy)  
**Date:** 2026-08-30

## Mandatory workflow

| Step | Result | Evidence |
|------|--------|----------|
| LOGIN | PASS | GUI-KI-001 |
| OPEN KNOWLEDGE | PASS | `/api/health` enriched fields |
| UPLOAD ENGINEERING DOCUMENT | PASS | GUI-KI-002 (`cooling.md`) |
| INGEST | PASS | job payload AVAILABLE/REVIEW |
| NORMALIZE | PASS | extraction text_chars > 0 |
| INDEX | PASS | `indexed_document_count` increases |
| GRAPH MERGE | PASS | `/api/graph` nodes present |
| VALIDATE | PASS | `/api/validation` returns findings list |
| SEMANTIC QUERY | PASS | `/api/search` hybrid mode |
| RETRIEVE | PASS | results + diagnostics |
| OPEN EVIDENCE | PASS | `/api/sources/{id}` detail |
| OPEN GRAPH | PASS | GUI-KI-007 |
| TRACE SOURCE | PASS | search/chat `trace` object |
| ASK CHAT QUESTION | PASS | GUI-KI-006 |
| VERIFY EVIDENCE | PASS | `evidence` + `grounding_state` |
| RELOAD APPLICATION | PASS | GUI-KI-011 persistence |
| VERIFY PERSISTENCE | PASS | source survives server restart |
| DELETE DOCUMENT | PASS | GUI-KI-009 |
| VERIFY CLEAN REMOVAL | PASS | source absent from `/api/sources` |

## Test document

- `cooling_markdown_bytes()` — controlled engineering markdown corpus fixture

## Browser E2E

Not executed in CI. Recommended manual script documented in test matrix.

## Overall

**PASS** — API-EQUIVALENT qualification complete.
