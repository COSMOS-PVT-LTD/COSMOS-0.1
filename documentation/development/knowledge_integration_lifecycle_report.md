# Knowledge Integration — Lifecycle Report

## States exercised

| Transition | Test | Result |
|------------|------|--------|
| Ingest → AVAILABLE (markdown) | KI-T02 | PASS |
| Ingest → REVIEW_REQUIRED (PDF) | `test_approve_source.py` | PASS (existing) |
| APPROVE_DOCUMENT | `test_approve_source.py` | PASS (existing) |
| DELETE source | KI-T04 | PASS |

## Authorization

- VIEWER ingest blocked: KI-T05 (403)
- Admin ingest allowed: KI-T02

## Deferred

- REJECTED → retrieval exclusion adversarial (covered in foundation tests)
- APPROVED → DEPRECATED (existing governance tests)

## Defects

None in lifecycle integration path.
