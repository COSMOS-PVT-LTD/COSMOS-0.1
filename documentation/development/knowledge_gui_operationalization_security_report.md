# Knowledge GUI Operationalization — Security Report

## RBAC

| Check | Result |
|-------|--------|
| Server-side ingest authorization | PASS — VIEWER blocked (403) |
| UI hiding not relied upon for security | PASS — integration test uses real viewer credentials |
| Admin delete/re-ingest | Preserved existing role checks |

## Provider boundary

| Check | Result |
|-------|--------|
| `provider_invoked` on health | false |
| `provider_invoked` on search | false |
| `provider_invoked` on chat | false |
| `provider_invoked` on validation | false |

## Credentials

- Qualification tests use bootstrap admin `cosmos-admin` / `COSMOS-Dev-2026!` (development only — D3 note from prior qualification carries forward)

## Error disclosure

- Classified error kinds in UI: USER INPUT, VALIDATION, INGESTION, RETRIEVAL, GRAPH, AUTHORIZATION, BACKEND UNAVAILABLE, INTERNAL
- No secrets or credentials exposed in error messages

## Frozen security modules

No modifications to authorization canonical modules beyond pre-existing uncommitted GUI work.

## Overall

**PASS WITH HARDENING** — RBAC enforced; provider boundary preserved.
