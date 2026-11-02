# Compact workspace launch recovery — 2026-10-30

## Incident and scope

The source launcher `scripts/launch_compact_engine.py` failed before opening its
native window. `SQLiteJobRepository.verify_integrity()` correctly refused a
missing retained STL blob. No integrity check was disabled.

Authority root: `output/picogk-components-2026-10-24/app-data/engineering_state/v1`.
Project: `bb7ebea6-15f9-43b8-b6c0-fd2a2d358155`.

Read-only inspection of all six existing content-hash reference tables found one
missing digest, referenced by `export.stl` attachments of two completed historical
jobs:

- `4ba4a122-2373-458e-ae9a-0a717b557ac1`
- `cf3511c1-ac72-4ddb-b85a-f50086463dee`

The reason the original file disappeared is not established. This repair does not
attribute it to cleanup, disk exhaustion, or any person.

## Exact recovery, not geometry substitution

The retained VDB at
`output/picogk-components-2026-10-24/app-data/picogk_component_candidates/job-8cd59583559d48fcb86344c36b95538f/source.vdb`
was read by a separate recovery worker, preserving the original field order,
encoding and header. Its SHA256 remained
`4b3b860732f22c5463a7d37273b91a2e478e44ee8befdd960cf5b07c3d0fa596`.

Recovered original STL:

- SHA256: `db02644594cf9bbced1796e4d7bb77fd44833dedc4ec712e6ebfa148916f4245`
- Bytes: `184726884`
- Triangles: `3694536`
- Original parts: `16`

This is the historical artifact, not the separate six-group compact redesign.
Recovery required the original byte length and SHA256, not visual or geometric
similarity. `plugins/geometry/workers/recover-pico-stl/` built separately with zero
warnings/errors; original qualified workers and runtime receipts were not edited.

`scripts/restore_exact_blob.py` defaulted to a read-only preview. Application bound
the exact preview hash
`5140bacf9134bc47765c03e0418157563cbf045edaab1d254109351dae381f27`,
acquired the coordinator lease and I/O lock, and used the existing atomic
put-if-absent storage path. The installed independent copy is mode `0600`, with
one hard link. The helper rejects existing destinations, wrong bytes, changed
previews, missing stores, and unsupported commit-byte recovery.

The restoration receipt confirms full durable-job integrity PASS, zero deleted
records, no migration, and unchanged metadata database SHA256:
`a09027930370712cc4130ac92f9e04a045045ec0960c7c5fa88390c53dcd00f5`.
The unchanged-database claim applies to the restoration operation, not subsequent
ordinary sign-in/audit activity.

## Launch behavior and verification

The launcher now reports a concise fail-closed integrity error with preservation
guidance if retained files are ever unavailable again. It does not reset the
store, bypass validation, initialize a replacement root, or stop occupied-port
listeners. Its stale startup message was corrected to distinguish regenerated
research CAD from still-pending matched physics and R08 acceptance.

The actual source command was launched on free loopback port `8898`. Native UI
inspection confirmed the COSMOS login window, successful existing-account sign-in,
Native Geometry workbench navigation, and loading of the existing authorized
project and retained component/PicoGK history. No `.app` bundle was installed.

## Exact historical preview inside the full desktop application

End-to-end inspection exposed a second, independent usability defect: the existing
preview required `upstream_current`, even when displaying an unchanged saved
geometry artifact. The component head remains `06f920dc-ff93-4aa3-8c74-a08c43f2bac3`
and the candidate head remains `dcf4adff-9540-443e-9e6e-a4775fab92fd`, with unchanged
compiler methods. Their upstream propulsion input advanced from
`3ce745d6-445a-4fca-81af-be9c09f200dc` to
`68e081b1-0b85-4cd0-b87d-b73bf30e572e`. Therefore this is historical geometry with
stale upstream physics, not a missing or changed geometry source.

`gui/static/engine-redesign.js` now supports a narrowly scoped, read-only historical
preview. Existing authenticated GET endpoints verify unchanged candidate and
component heads, exact source payload/hash, and the saved recipe/compiler methods.
The local STL must still match its manifest checksum, source commit and recipe.
Unsaved/dirty drafts, superseded geometry heads, changed methods and mismatched
artifacts remain refused. No POST, baseline change, source rebinding or freshness
flag assignment was added.

Both adjacent preview status and main status show **HISTORICAL / NOT CURRENT**.
The expanded CAD viewer title retains that warning. Errors are now displayed beside
the preview as well as in the main status, rather than being easy to miss above a
long parameter table.

Actual native desktop verification loaded these existing local files:

- `output/engine-redesign-regenerated-2026-10-30/display/DISPLAY-ONLY-export.stl`
- `output/engine-redesign-regenerated-2026-10-30/display/manifest.json`

The UI confirmed exact recipe/source/checksum matching and rendered all six parts,
199,792 display triangles, with XYZ axes and CAD viewing controls. The display is a
reduced derivative, not metrology or the original native engineering mesh. The full
COSMOS window was left open in expanded historical-preview mode.

Screenshot: [COSMOS_ENGINE_PREVIEW.png](COSMOS_ENGINE_PREVIEW.png).

## Evidence

All paths below are repository-relative; large recovery artifacts remain outside
the source/evidence tree.

- `output/COMPACT_LAUNCH_RECOVERY_2026-10-30/recovery-attempt.json`
- `output/COMPACT_LAUNCH_RECOVERY_2026-10-30/restore-preview.json`
- `output/COMPACT_LAUNCH_RECOVERY_2026-10-30/restore-applied.json`
- `output/COMPACT_LAUNCH_RECOVERY_2026-10-30/integrity-regression-final.xml`

Targeted recovery, launcher, durable-job and project-authority regression suite:
**112 passed**. Ruff checks and formatting passed for the changed recovery and
launcher Python files. Independent code review found and prompted explicit
rejection of commit-byte recovery, which is outside this helper's scope; the
current job-artifact restoration was unaffected.

Targeted research-display guard, CAD workspace and viewing-tool JavaScript suite:
**34 passed**; JavaScript syntax checks passed. These are scoped checks, not a
whole-repository test or remote CI claim.

After closing the running native window, launch again from Terminal with:

```sh
cd /Users/vaibhavkumarn/Desktop/COSMOS/COSMOS_0.1
.venv-release-p12/bin/python -m scripts.launch_compact_engine
```

An occupied-port message means an existing viewer is still using that port; it is
not permission to terminate an unrelated process. Preview file selection is session
state: reopen the same display mesh and manifest when starting a fresh session.

This is workspace/data recovery and software verification. It does not establish
matched thermal/feed closure, manufacturing release, physical validation or R08
acceptance.
