# Optional local Native Geometry workbench

P08 is a real native, independently QA-checked **software-fixture vertical slice**. It is not a general CAD editor, rocket-engine geometry generator, manufacturing export, engineering publication or physical validation facility.

Enable only in an explicitly qualified local developer environment:

```sh
COSMOS_NEW_SHELL=1 COSMOS_NGG=1 COSMOS_NGG_RUNTIME_CONFIG=/absolute/path/to/qualified-local-runtime.json python -m gui --root /absolute/path/to/isolated-state --headless --port 8812
```

Use the application's existing launcher/root/port options where applicable; `gui.server`'s public wiring function remains `serve_application(root, host='127.0.0.1', port=8780)`. The repository's reproducible isolated launch is `tests/ui/ngg/serve_fixture.py`; do not point it at user application storage. No native auto-install or runtime autodetection occurs. Both feature flags default off. Missing/invalid G5 receipt, missing dependencies or hash drift fail closed. Runtime paths in retained evidence are ephemeral local **test** installations, not a production deployment recipe. No upstream native license, signing, redistribution or other-platform acceptance is implied.

## Controls and authority

- Feature tree, fixed SI-reference parameter inspector, separate source/representation labels, global shell project controls and geometry-specific immutable project/revision/hash context.
- Engineer/Admin can change qualified sphere/Boolean operation, backend and explicit PicoGK voxel size. Other roles are read-only and cannot launch builds/reimports. Reference radii/centres cannot be freely edited; arbitrary client geometry/paths/commands are rejected.
- Undo/redo activates existing server-owned immutable revisions. Shell UI preferences are not scientific state. Browser reload retains the session context and job; server restart deliberately ends this ephemeral qualification session.
- Real bounded build queue and cancellation; independent QA is required before display/exchange. No invented percentage. A stale, rejected, missing, tampered or foreign-actor candidate cannot be exchanged/reimported.
- WebGL arrows rotate, +/- and wheel zoom, F fits; front/side/top and visual-X clip. Clipping is display-only, not a CAD section operation. Source STEP is analytic; coarse STEP display triangulation is **not** the exported geometry. PicoGK STL display shows the actual accepted tessellation.
- Two picked/indexed display vertices are measured on the server with explicit SI output. These samples are not analytic feature metrology. Bounds identify their reference/QA source.
- Focus mode hides distracting shell docks **only for this workbench/session**, automatically on narrow screens; it does not alter saved shell preferences. Existing shell resize/theme/font controls remain available.
- Fixture exchange wizard states file representation/tolerances/voxel size, exact snapshot and source/export SHA256. Downloaded bytes remain Accepted candidates, not Published artifacts. `GeometryBuildService.export()` remains fail-closed. Reimport accepts only exact matching downloaded bytes and repeats independent QA.
- Exact snapshot/graph/source/request, build events, QA and reimport receipts are inspectable. Diagnostics contain a code, cause and recovery. No fabricated human engineering signoff.

Rollback: unset `COSMOS_NGG` (or set `0`); native route/API/catalog item disappear and no workspace is created. Existing modern/legacy workbenches keep their routes and functionality. Unset `COSMOS_NEW_SHELL` for complete legacy-shell rollback. Do not delete stored engineering designs or native candidate folders as a rollback step.

Evidence and limits: `docs/implementation/evidence/P08_2026-10-09/P08_IMPLEMENTATION_REPORT.md` and `G6_GATE.json`. Formal UX/CAD owner review is still required before product acceptance; native release/security/distribution gates are separate.
