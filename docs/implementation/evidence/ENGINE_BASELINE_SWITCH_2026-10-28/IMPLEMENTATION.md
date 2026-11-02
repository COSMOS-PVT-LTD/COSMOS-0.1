# Compact CAD development baseline switch

User approval: replace the active development baseline with the compact redesign,
retaining the original source/history rather than deleting dependency records.
R08 engineering qualification remains ON HOLD. A development default is not
manufacturing, physical, material, seal or hot-fire acceptance.

## Intended exact scope

- Existing CAD project: `bb7ebea6-15f9-43b8-b6c0-fd2a2d358155`.
- Existing source component: `afc95eb3-2d0c-55b7-95eb-2644f67e01d0`.
- Exact retained source commit: `06f920dc-ff93-4aa3-8c74-a08c43f2bac3`.
- Existing app root: `output/picogk-components-2026-10-24/app-data`.
- Separate default `cosmos_app_data` project `d7bcfc43-d4ce-44af-be49-5a92bf2ad942`
  has no component CAD. Do not migrate/switch that root or silently attach this
  project's geometry to its calculations.

## Implementation

- `systems/geometry/development_baseline.py`: one project-scoped, immutable-
  revision selection record; exact candidate/source dependencies; expected-head
  concurrency control; currentness checks before and after save; idempotent
  operations; retained selection history; explicit rollback to the preceding
  usable selection, including the original component on the first switch.
- `api/engine_redesign.py`: authenticated `active-baseline`, `history` and
  `rollback` actions. No purge, runtime-admission or engineering-release route.
- `gui/static/engine-redesign.js`: opens the exact selected candidate on project
  load; retained source editor is accessible but not the compact development
  default; explicit select/rollback/history controls; identity/freshness badges.
  Rocket workflow displays a CAD-baseline link and warns that existing physics
  results/artifacts are not automatically matched to the new geometry.
- `scripts/select_engine_development_baseline.py`: explicit existing root,
  project, stable active local account and source; exclusive coordinator lease;
  source-bound preview SHA256 required for applying; no account bootstrap,
  native builds, discovery, migration or deletion.

Saving a later candidate does NOT silently advance the selected baseline. Its
existing exact selection becomes noncurrent until explicitly reconciled. Old
calculations, native outputs and receipts retain their old source identities.

Application evidence is recorded below and in the adjacent JSON receipts. The
earlier redesign development report is a historical snapshot, not a baseline-
switch receipt.

## Applied selection

The explicit method-pinned preview `preview-v2.json` was applied using SHA256
`fab1e0faae959979214971dc5c20e56870ef3f2d6139c866c5d85aa5cb1269c1`.
`preview.json` is the earlier diagnostic draft before method-source pinning;
it was not applied. No historical receipt was changed to accept this selection.

- New candidate object: `c5fa70b5-6fa6-55c2-ad0e-6c37a6de84cb`.
- New exact candidate commit: `dcf4adff-9540-443e-9e6e-a4775fab92fd`.
- Development selection commit: `2afd02ce-36b8-4939-b71b-c5f8d7872d6a` (v1).
- Selection scope: `PRELIMINARY_GEOMETRY_DEVELOPMENT_ONLY`.
- Source retention: `RETAINED_IMMUTABLE_NOT_DELETED`.
- Readback was CURRENT as freshness only, not engineering acceptance.
- `applied.json` includes the exact source-bound research generation input.

`preservation.json` verifies all 7 prior object heads and all 9 prior commits are
unchanged; 2 new heads/commits were added, 0 records were deleted, and separate
default app-data metadata remains SHA256
`9ab89201846dfdc581e3fd4ffd5cf98258952b20c5818d9d22bead3ef713aeac`.

The selected candidate integrates the existing collector/body operands and nine
return segments into 6 metal groups while retaining the approved source gas
path and hydraulic bores. It does not invent optimized dimensions or establish
efficiency improvement. Smooth transitions, matched thermal/feed analysis and
full regenerated/qualified engine CAD remain unfinished engineering work.

## Verification and use

The final focused Python geometry/governance/launcher regression passed **148
tests**, zero failures/errors/skips. JavaScript regression passed **15 tests**.
JUnit: `output/compact-engine-software-2026-10-28/baseline-final-regression.xml`.
All 11 currently stored commit payloads passed SHA256 verification, and the
actual selected baseline read back CURRENT under the unchanged source head.
The existing OCCT component and PicoGK profiles still have zero pinned source
hash differences; these profiles do not admit the new compact generator.
Full read-only admission of both existing legacy runtime profiles also passed.
No full engine build or R08 campaign was run. The 10 GiB full-build guard remains
in force; only approximately 7 GiB was available during this change.

The verification skill traced UI selection -> authenticated HTTP -> managed
snapshot -> response/default reload in a temporary test repository. Manual UI
checks confirmed selection, reload to the exact active candidate, hidden-but-
accessible retained source, rollback, re-selection/history and the rocket
workflow's separate CAD/physics identity warning. Observed browser error log was
empty. The test project is not engine evidence.
Screenshot: `BASELINE_WORKSPACE.png` (isolated test selection, not an engine build).

Launch this exact existing development project (without changing the default
data root), from the checkout:

```sh
.venv-release-p12/bin/python -m scripts.launch_compact_engine
```

Open:
`http://127.0.0.1:8898/app/workbench/native-geometry?project=bb7ebea6-15f9-43b8-b6c0-fd2a2d358155`

The launcher refuses an occupied port, missing data or missing legacy profiles;
it never kills a viewer, creates a replacement store, runs a native build or
resumes qualification. `--port` can select another free unprivileged local port.
No existing viewer was restarted by this change.
