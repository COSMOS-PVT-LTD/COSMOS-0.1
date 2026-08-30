# Knowledge Integration — Security Report

## Offline / IP

| Check | Result | Evidence |
|-------|--------|----------|
| provider_invoked=False | PASS | production + compat tests |
| No mandatory cloud in qualification path | PASS | local backends only |
| Unauthenticated API blocked | PASS | KI-T01 |

## RBAC

| Check | Result | Evidence |
|-------|--------|----------|
| Server-side ingest denial for VIEWER | PASS | KI-T05 (403) |
| Session required for knowledge API | PASS | KI-T01 |

## Security finding (D3)

**S-001: Bootstrap development administrator**

- Path: `api/authentication.py` `_ensure_bootstrap_admin()`
- Credentials: `cosmos-admin` / `COSMOS-Dev-2026!`
- Active on normal login path
- **Classification:** Development bootstrap credential — must not be treated as production-ready
- **Action:** Document; rotate/disable for production deployment (deferred — requires human policy)

## Path traversal / upload

Validated by `knowledge/workspace/security.py` (existing unit tests).

## Frozen blocks

Not modified.
