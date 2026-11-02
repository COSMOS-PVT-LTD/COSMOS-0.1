# P08 scoped vertical slice, conditional on G5 closure

## Verified reuse and boundaries

- `gui/server.py:CosmosApplication`, `CosmosApplicationHandler`: existing authenticated local shell and DesignStore; no new design store.
- `gui/app_shell.py:inject_shell`, `gui/static/app-shell/{model,adapter,shell}.js`: default-off modern shell, known-route navigation, themes, project/revision and dock preferences.
- `gui/static/design-system/components.js`: ProjectTree, ParameterTable, EngineeringStatus, JobMonitor, ErrorDetails, EvidenceLink. Reuse token colours and accessible focus styles.
- `systems/contracts/geometry/`: immutable P06 SI snapshots/graphs/requests/build records. Remain authoritative for geometry lineage.
- `systems/geometry/service.py`: bounded real asynchronous candidate builds, cancellation, independent QA, fail-closed nonpublication.
- `plugins/geometry/{adapters,protocol}.py`, `infrastructure/geometry/supervisor.py`: real optional native worker processes, fixed operator commands, bounded queues/time/resources.
- `tests/fixtures/ngg_cases.py`: approved synthetic fixture policy only. Promote reusable definitions to Systems; never import test modules from the application.

## File-scoped sequence

1. Close G5 with all original native fixtures, extra wrong-radius rejection, immutable retained exports, independent re-audit and new decision receipt. Preserve historical P07 failed evidence.
2. Add `systems/geometry/software_fixtures.py` and `workbench.py`: reusable fixture definitions, ephemeral actor-scoped immutable revisions, exact lineage, worker-backed queue, bounded mesh preview, server-side measurements, explicit **software-fixture exchange** and independent reimport.
3. Add `gui/ngg.py` and focused hooks in `gui/server.py`: strict `COSMOS_NGG` defaults off, explicit hash-checked local runtime config, loopback/Host/Origin/auth guards, request size/schema checks, no client-supplied worker paths or arbitrary geometry.
4. Add `gui/static/ngg/{model,viewport,view}.js`, `styles.css`, and `workbench/native-geometry.html`: feature tree, bounded SI inspector, real mesh WebGL viewport, rotate/fit/orthographic views/clip section, server measurements, undo, build/cancel queue, QA, fidelity-labelled fixture download and upload/reimport, snapshot/evidence access.
5. Extend modern shell navigation only with a server-advertised enabled catalog item. Flag-off catalog and legacy routes stay unchanged.
6. Add Python/JS/HTTP/browser negative tests, real two-backend build-inspect-download-reimport snapshot evidence, axe and viewport performance, before/after screenshots. Re-run regression and physics parity. Store evidence under `P08_2026-10-09/`.

## Explicit scope decision

The qualified P07 service does not build arbitrary rocket-engine geometry and has no trusted engineering review/publication. The smallest honest slice therefore exposes the existing **synthetic software-fixture project** with fixed 10mm reference dimensions and editable fixture operation/backend/declared voxel size. Other shell projects remain visible but are not relabelled as geometry inputs. Free-form CAD, arbitrary radius edits, engineering export/publication, simulation/hardware handoff, native distribution and human acceptance remain blocked. A separately named fixture exchange copies only accepted, current, hash-verified candidate bytes; it never changes P06 publication state or bypasses `GeometryBuildService.export()`.

This is not a new scientific storage authority. Workbench sessions are ephemeral, explicit local qualification tools. Immutable revisions are server-held P06 DTOs; browser preferences and undo commands are presentation-only. No scientific equations live in GUI code. No new app dependency, native autoinstall, broad repo redesign or production native activation.

## Acceptance

Software G6 requires real native E2E for both backends, exact snapshot/hash links, missing/stale/rejected/tampered artifacts denied, cross-actor/Host/Origin/oversize/path attacks denied, flag-off compatibility, responsive/keyboard/a11y checks and measured viewport loading. Formal UX/CAD owner acceptance is separate and cannot be fabricated by the implementer. If any software criterion fails, P08 remains partial.
