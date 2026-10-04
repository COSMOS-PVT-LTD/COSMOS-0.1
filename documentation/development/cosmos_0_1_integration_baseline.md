# COSMOS 0.1 Integration Baseline

Date: 2026-09-03  
Branch: `main`  
Status: local computational engineering application — **not** flight-certified.

## Current architecture

```
GUI (html/css/js) → API (DTO/auth) → Systems (workflow/design) → Physics → Core
```

GUI does not import Physics. Browser `sessionStorage` / `localStorage` are convenience only.

One design state (`PropulsionDesign`), one workflow graph (`systems.workflow.graph`), one persistence store (`DesignStore`), one result/V&V contract (`CalculationResult`).

## Runtime commands

```text
python main.py
python main.py --browser
python main.py --headless --port 8780
```

Bootstrap login (ADMIN profile):

```text
cosmos-admin
COSMOS-Dev-2026!
```

The ENGINEER login profile rejects this account (`error_code: profile_mismatch`).

Knowledge standalone server:

```text
python -m knowledge.workspace
```

Port 8765 is development-only and unauthenticated. Use the desktop application for governed knowledge access.

## API routes (propulsion)

| Method | Path | Role |
|---|---|---|
| GET | `/api/propulsion/designs` | list summaries |
| POST | `/api/propulsion/designs` | create |
| GET | `/api/propulsion/designs/{id}` | open |
| POST | `/api/propulsion/designs/{id}/save` | persist |
| POST | `/api/propulsion/designs/{id}/clone` | save-as |
| POST | `/api/propulsion/designs/{id}/requirements` | edit targets |
| POST | `/api/propulsion/designs/{id}/propellants` | registry IDs |
| POST | `/api/propulsion/designs/{id}/cycle` | record class only |
| POST | `/api/propulsion/designs/{id}/run/phase3` | OP / thermo / performance |
| POST | `/api/propulsion/designs/{id}/run/phase4` | chamber / thermal / structure / nozzle |
| POST | `/api/propulsion/designs/{id}/run/phase6` | summary / consistency / review |
| GET | `/api/propulsion/designs/{id}/workflow` | graph + result status |
| GET | `/api/propulsion/designs/{id}/stages/{stage}` | stored result |
| GET | `/api/propulsion/designs/{id}/export` | package |
| GET | `/api/propulsion/workflow-catalog` | stages 00–16 |
| GET | `/api/catalogs/propellants` | Physics registry |
| GET | `/api/catalogs/materials` | Physics handbook |
| GET | `/api/workbenches/rocket-engine/suite` | physics-tool modules |

Quantity fields accept `{magnitude, unit_symbol}` including `bar`, `kN`, `kPa`, `MPa`.

Canonical fuel id is `RP1` (`RP-1` is an alias).

## Workbench routes

| Route | Status |
|---|---|
| `/app/workbenches` | hub |
| `/app/workbench/rocket-engine` | live |
| `/app/workbench/knowledge` | live (Maharshi Bharadwaj) |
| `/app/help` | live |
| remaining hub cards | planned pages, not fake live tools |

## Rocket Engine workflow (00–16)

Presentation order is `PROPULSION_STAGE_SEQUENCE`. Graph edges remain the execution authority.

| Index | Stage | Implementation |
|---|---|---|
| 00 | Design project | PARTIAL — identity / persistence |
| 01 | Requirements | IMPLEMENTED |
| 02 | Propellants | IMPLEMENTED (registry identity) |
| 03 | Cycle | NOT_IMPLEMENTED |
| 04 | Operating point | IMPLEMENTED |
| 05 | Thermochemistry | PARTIAL (CEA unbound) |
| 06 | Performance | PARTIAL (choked isentropic) |
| 07 | Injector | NOT_IMPLEMENTED |
| 08 | Chamber | PARTIAL (L* geometry) |
| 09 | Thermal | PARTIAL (Bartz) |
| 10 | Cooling | NOT_IMPLEMENTED |
| 11 | Nozzle | PARTIAL (1D stations; no MOC) |
| 12 | Structure | PARTIAL (thin-wall) |
| 13 | Materials | PARTIAL (handbook catalog) |
| 14 | Performance summary | IMPLEMENTED (aggregation) |
| 15 | Consistency | IMPLEMENTED |
| 16 | Design review | IMPLEMENTED (`READY` / `INCOMPLETE` / `BLOCKED`) |

Documented bypasses (`BYPASSABLE_WHEN_UNIMPLEMENTED`): chamber←injector, nozzle←cooling, operating_point←cycle.

## Current capability matrix

| Capability | State |
|---|---|
| Login / session / RBAC | live |
| One persisted `PropulsionDesign` | live |
| bar / kN requirements | live |
| Physics adapters (isentropic, area-Mach, Bartz, thin-wall) | live |
| Phase 3/4/6 orchestration | live, honest `phase_status` |
| Injector orifice design | NOT_IMPLEMENTED |
| Regenerative / film cooling | NOT_IMPLEMENTED |
| Cycle power balance | NOT_IMPLEMENTED |
| Nozzle MOC / Rao contour | NOT_IMPLEMENTED |
| NASA CEA | UNAVAILABLE |
| Ten other hub workbenches | planned |

## State model

Design `status`: `draft` | `active` | `archived`.

Stage result status: `NOT_CALCULATED` | `CURRENT` | `STALE` | `FAILED` | `NOT_IMPLEMENTED`.

Phase payload: `ok` plus `phase_status` `COMPLETE` | `PARTIAL` | `FAILED`.

Phase 4 may be `ok=True` and `phase_status=PARTIAL` when injector/cooling are NOT_IMPLEMENTED.

## Revision model

`PropulsionDesign.record_input_change` increments `revision`, appends `change_log`, invalidates dependents.

## Invalidation model

`systems.workflow.invalidation.INPUT_FIELD_ROOTS` maps fields to a graph root. Dependents with CURRENT results become STALE (not deleted).

Derived subsystem slots (`nozzle_design`, `chamber_design`, …) keep last numbers and set `geometry_status=STALE`. Recalculation writes `geometry_status=CURRENT`.

## Persistence model

`cosmos_app_data/propulsion_designs/*.json` via `DesignStore` (temp file + replace, thread lock). List summaries are sorted by `updated_at` descending.

Knowledge is a separate vault.

## V&V semantics

Verification may be software-identity or catalog lookup. Validation is `NOT_CLAIMED` unless a stored experimental contract exists.

Design Review `review_ready` is true only for verdict `READY`. Injector, cooling, and cycle keep a design `INCOMPLETE`.

CANDIDATE knowledge answers are prefixed `UNREVIEWED CANDIDATE`.

## Test commands

```text
python -m pytest
python -m pytest tests/integration_tests/gui/test_propulsion_e2e_http.py
python -m ruff check api systems
```

CI: the `test` job is fail-closed. Ruff on `api`/`systems` is fail-closed. Ruff/mypy on frozen Core/Physics/Knowledge are reported with step-level `continue-on-error`.

## Known limitations

- Injector, regenerative cooling, cycle power balance, MOC contour, and CEA are not implemented.
- Ten hub workbenches remain planned.
- Standalone knowledge `:8765` is unauthenticated (banner only).
- Native pywebview failure falls back to the system browser; it does not exit the process.
- Historical ruff/mypy debt in Core/Physics/Knowledge is not part of the fail-closed gate.
