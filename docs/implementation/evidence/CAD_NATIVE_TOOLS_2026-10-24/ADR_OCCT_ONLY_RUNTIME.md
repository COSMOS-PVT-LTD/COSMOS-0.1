# ADR: separately qualified OCCT-only component research profile

Status: approved by the user and implemented, 2026-10-24.

## Context

The earlier combined NGG runtime manifest depended on temporary PicoGK, .NET and native files that no longer exist. Native component building and retained-solid inspection require OCCT, but do not require enabling PicoGK reference fixtures. Rewriting a historical combined receipt, substituting a different executable or treating a missing runtime as passing would invalidate provenance.

The user was asked whether a separately qualified OCCT-only profile could be admitted for these CAD tools and component rebuilding, while keeping PicoGK disabled and historical receipts unchanged. The answer was **“Approve separately qualified OCCT-only profile.”** This is approval of that admission policy, not approval of manufacturing, hot-fire, migration or production release.

## Decision

- Add schema `cosmos.occt-component-runtime.v1` in `api/occt_component_runtime.py`.
- Preserve the existing combined runtime admission unchanged; branch only on the explicit new schema for component building.
- Require pinned interpreter, server-owned worker/reader commands, exact current component policy/version/method hashes, receipt integrity and sufficient real passing native/component-HTTP/driver JUnit reports with zero failures/errors/skips.
- Explicitly keep `picogk_enabled=false`, `production_enabled=false`, physical validation NOT_PERFORMED.
- Independently qualify inspection/drawing using `cosmos.cad-tools-runtime.v1` as defined by `systems/geometry/cad_tools.py`. This receipt is not substituted for component qualification.
- Suppress the combined fixture/PicoGK laboratory in an OCCT-only application. Its authenticated API returns `FIXTURE_PROFILE_DISABLED`; it does not attempt G5 admission or imply fixture availability.
- Use the isolated `.venv-cad-inspection/` and exact `requirements-cad-inspection.lock.txt`; no native packages are injected into the application environment.
- Exercise saved component rebuilds and browser inspection/export on a new task-only SQLite/filesystem copy; do not switch or migrate the owner's root.

## Evidence

Current component profile: `component-runtime/runtime.json` and its append-only software receipt.
Current inspection profile: `inspection-runtime-v2/runtime.json` and its append-only software receipt. The earlier inspection-runtime receipt remains unchanged; v2 records the newly verified JSON attachment fix.

See `IMPLEMENTATION_AND_VERIFICATION.md` for exact tests, model/job/BREP identities and evidence. The real 16-body source rebuilt successfully and passed its declared STEP/STL software checks. Unit and HTTP tests explicitly reject unauthorized runtime changes and accidental combined-fixture enablement.

## Consequences

Frozen module layering is unchanged. Source-method changes correctly make older models/builds historical rather than upgrading their claims. A native runtime can now be admitted for this explicit research scope without pretending that PicoGK or production readiness is available.

The profile is machine-local, opt-in, hash-pinned and fail-closed. A changed method/runtime/report requires a new qualification directory. No supplier seal acceptance, process-specific structural allowables, experimental validation, generalized CAD solver or manufacturing approval follows from it.
