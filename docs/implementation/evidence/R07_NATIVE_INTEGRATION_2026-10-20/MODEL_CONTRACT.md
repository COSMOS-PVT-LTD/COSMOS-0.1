# Selected R07 nozzle candidate contract

This increment integrates the previously saved engine-derived divergent-nozzle **intent** with a separately qualified native build policy. It does not complete every broader NGG-01–12 requirement or grant engineering/manufacturing/physical acceptance.

## Source and representation

- Exact authorized current `engine-geometry-intent` commit and compare-and-swap head. Its current baseline/nozzle result and method dependencies must be usable. No latest-design substitution or baseline mutation.
- Existing P06 `DesignSnapshot`, `GeometryFeatureGraph`, `GeometryBuildRequest`, build records/events/reports/artifacts. Namespace `engine-design-{design_id}`, separate from fixed sphere/Boolean fixtures.
- Immutable typed SI stations and three explicit lengths: radial wall thickness, source tolerance, export tolerance. The native envelope accepts **2–129** strictly increasing axial/radial stations; intent capture alone may retain up to257, so larger intents are explicitly refused for native V1 rather than downsampled.
- `throat-x`: right-handed identity frame, throat at x=0, axis +X. One planar closed meridian consisting of the retained inner polyline, exit radial end, outer polyline at constant **radial offset**, and throat radial end. Full revolution creates a one-body open-bore wall solid. It is not normal wall thickness or a structural sizing result.
- The profile is piecewise linear through saved stations, **not** the original continuous bell curve. No chamber, convergent, injector, channels, interfaces, arbitrary placement or representation conversion is inferred.
- Native size envelope: length≤3m, outer radius≤1m, inner radius≥10µm, radial thickness1µm–0.1m, segment Δx>1nm; no healing/repair. Source tolerance≥0.1nm; export tolerance≥0.1µm; both below half the radial thickness. Those floors are not a guarantee of downstream engineering accuracy; actual exported geometry must pass explicit QA.

## Native and independent software checks

`plugins/geometry/workers/nozzle_worker.py` uses pinned OCP7.8.1.1 / OCCT7.8.1, closed profile→face→full X-axis revolution, checks one valid solid, retains native B-rep and exports paired STEP and binary STL. All source values are metres, kernel coordinates millimetres; exchanges are explicitly metres. No mesh is relabelled analytic STEP. The full-revolution API is documented by [OCCT](https://occt3d.com/dev/doc/refman/html/class_b_rep_prim_a_p_i___make_revol.html); qualification uses the actual installed pinned API, not the current documentation version.

`systems/geometry/nozzle_reference.py` independently integrates `π[(r+t)²−r²]` and its axial first moment on each source segment. Its signed surface distance is the exact meridian-polygon distance for this axisymmetric reference, not a CAD-kernel measurement. Retained stations, segment midpoints, throat/exit annular samples and eight azimuths define the documented reverse sampling set.

Users must provide finite positive, source-labelled ceilings for relative volume [1], centroid distance [m], and sampled surface/bounds distance [m]. The GUI supplies no engineering defaults. Qualification values belong to manufactured software tests only.

- STL: metre header, finite actual triangle vertices/normals, nondegenerate/unique faces, consistent edge orientation, two incident faces per edge, one connected component, positive signed enclosed volume, **Euler characteristic0** (a through-bore wall is not a sphere), analytic volume/centroid discrepancies, vertices/face-centroids→reference and reference→actual planar triangle sampled distances. Conservative AABB rejection only removes triangles that cannot satisfy the declared distance ceiling; unmatched samples fail. Exact planar distances are used, not nearest vertices. Budget/cancellation checked in bounded batches.
- STEP: separate pinned Gmsh4.15.0 process, no auto-fix, explicit units, one body, expected2N boundary faces, two planar annular end faces and allowed analytic carriers; imported mesh edge/orientation/Euler checks, analytic volume/centroid/bounds and bidirectional sampled surface checks. Response field types, finite dimensions, sample shapes and resource envelopes are validated before acceptance.
- Gmsh and OCP **share OCCT**. This is separate-tool/API/process/import evidence plus a kernel-independent formula reference, not a different-kernel comparison. Neither sample set is a certified Hausdorff bound or universal self-intersection proof.

## Authority and lifecycle

`engine-nozzle-build` / `cosmos.engine-nozzle-build-input.v1` captures exact intent bytes/commit/hash, snapshot/graph/request, explicit QA/source, methods, runtime identities and original command before asynchronous admission. Existing R05 repository membership, immutable blobs, CAS, leases, attempts, stage transcripts, retry/cancel/recovery and stale selection guards are reused. Stage append **including exact retries** must match the admitted domain/schema/namespace. No store migration was added.

Native execution uses the existing one-worker/two-queued supervisor,60s child timeout,1GiB observed-RSS guard and bounded output; native operations are out of the GUI process. STL QA has a60s budget and cancellation checks. Shared host coordination keeps its existing two-worker executor and project/storage quotas; arbitrary flood/maximum-workload certification is not claimed. At most16 distinct explicit QA profiles exist per application lifetime.

Completed software-QA candidates retain STEP/STL/B-rep originals, stage transcript and diagnostics. Only an exact current source/method/runtime and current selected attempt is labelled a current generated candidate. Unavailable/changed runtimes, stale sources, revoked access, cancellations and failed QA cannot manufacture a current accepted answer. Runtime removal does not make already retained originals unreadable. Preview triangles are derived from the exact retained STL; clipping/picking/keyboard tools are display-only.

Native `accepted` is explicitly **software-candidate QA**, not human engineering acceptance. API/UI/download headers retain `engineering_export_eligible=false`, `published=false`, engineering acceptance and physical validation `NOT_PERFORMED`. No simulation handoff or manufacturing release is added.

## Remaining broader R07 scope

Additional sourced component templates; general feature editing/undo; extrude/channel/placement and nonidentity transform qualification; analytic metrology; semantic regions/material/interface and named-selection remapping; study handoff; human evidence-bound acceptance/publication; maximum/representative-workload qualification. These remain open, not passed by this selected nozzle integration.
