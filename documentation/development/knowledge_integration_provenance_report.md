# Knowledge Integration — Provenance Report

## Chain

```text
chat conclusion
  → evidence[] (API response)
  → document_ids[]
  → source manifest + vault originals
  → content hash in manifest
```

## Verified (KI-T02)

- `document_ids` contains ingested `source_id`
- `evidence` array non-empty for factual query
- `GET /api/sources/{id}` returns `text_content` traceable to upload

## Graph provenance

- Source appears as graph node with same `source_id` (KI-T02)

## Findings

| ID | Finding | Class |
|----|---------|-------|
| P-001 | Foundation corpus may supply generic evidence when `document_ids` empty (KI-T07) | D5 — expected; not user-document provenance |
| P-002 | Chat UI truncates evidence display to 80 chars (`maharshi.js`) | D3 — UX, not backend defect |

## Defects fixed

None required for provenance integrity on user-uploaded documents.
