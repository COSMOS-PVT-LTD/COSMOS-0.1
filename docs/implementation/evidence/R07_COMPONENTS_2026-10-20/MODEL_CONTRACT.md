# R07 component/editor/study-handoff V1 contract

This extends, and does not replace, the qualified fixed-fixture and divergent-nozzle paths. It is bounded geometry software, not a complete engine CAD/CAE or hardware qualification system.

## Implemented geometry

| Feature | Actual construction | Explicit scope |
|---|---|---|
| Chamber / convergent / throat / nozzle | Closed, piecewise-linear meridian revolved into a bored wall solid | Exact saved chamber and divergent stations plus user-supplied wall/convergent/throat-land dimensions; no hidden resampling or inferred structural sizing |
| Solid axisymmetric profile | Closed meridian revolved about local +X | Explicit zero inner radii; not an arbitrary solid modeller |
| Internal regenerative passages | Axial, contour-following, constant-angular-width/radial-depth sectors actually subtracted from the wall | Explicit hot ligament, roof/rib clearance, count, depth, phase; optional separate closed coolant-volume solids |
| Showerhead | Real plate with a uniform ring of through-drilled holes | Geometry, not injection performance or a qualified head/manifold |
| Impinging doublet / triplet | Real plate with paired inclined bores; triplet adds the centre axial bore | Bore/plate containment and separation checked; no atomization/stability model or propellant allocation |
| Shear coaxial | Separate concentric inner/outer tube solids with explicit gap | No claim of mixing, recession, swirl or manifold design |
| Continuous-gap pintle | Separate hollow stem, outer sleeve and centre rod/conical deflector | Static geometric assembly, not throttling/flow/stability qualification |
| Rigid placement | Proper frame-tree transform of explicitly selected predecessor parts | Explicit translation and right-handed rotation, no reflection or accidental fusion |

The pintle/coaxial naming follows public geometric terminology; no dimensions or performance defaults are taken from a published injector. Concept references: [NASA coaxial injector discussion](https://ntrs.nasa.gov/api/citations/20050217144/downloads/20050217144.pdf), [NASA pintle discussion](https://ntrs.nasa.gov/api/citations/19940018555/downloads/19940018555.pdf?attachment=true). These references are not validation evidence for COSMOS-generated hardware.

Helical/serpentine passages, inlet/outlet manifolds, swirl injectors, arbitrary extrusions/fillets, mechanical mounting/joining, multiphase flow, combustion stability, manufacturing allowances and mesh/CFD/FEA execution are explicitly unsupported in this V1 profile. Existing rectangular-channel thermal calculations are **not** silently mapped to the new sector-channel CAD. The existing cylindrical chamber L* approximation is retained and labelled; this does not introduce a new convergent-inclusive chamber-volume closure.

## Ownership and exact sources

- Systems: `systems/geometry/component_model.py`, `component_reference.py`, `component_sections.py`, `component_qa.py`, `component_authority.py`, `component_review.py`, `component_workspace.py` own intent, formulas, graph impact, orchestration and review.
- Plugins: `plugins/geometry/component_protocol.py`, `component_adapter.py`, `workers/component_worker.py`, `workers/component_step_reader.py` own pinned native execution/reimport. OCCT shape identity and Boolean/revolve construction history bind native faces; semantics are never guessed from face enumeration.
- Infrastructure: existing project snapshots, immutable commands/CAS, dependencies, durable jobs/stages/blobs and bounded supervisor remain authoritative. No database migration or live-root switch is introduced.
- API: `api/component_geometry.py` composes the four new domain routes; `api/nozzle_geometry.py` retains default-compatible shared candidate presentation.
- GUI: `gui/static/component-geometry.js` and `.css` provide typed editing, profiles, frames, explicit operands/outputs, validation/impact, revision restoration, session undo/redo, history, preview and review/setup controls. Both Native Geometry and Projects & Mission expose it. Original fixture tools remain in a separate labelled laboratory.
- Study contracts: `simulation/component_handoff.py`, separate from the unchanged sphere-only simulation handoff. A component setup is **not runnable** through that sphere solver.

Every model retains its exact baseline commit/bytes and SI snapshot/graph. Every build retains the exact model, request, explicit QA criteria, source/runtime hashes, original bytes and stage transcript. Editing a model/baseline or changing methods/runtime makes downstream selections/reviews/setups stale without deleting historical evidence. Restoration makes a new immutable commit and cannot silently rebind an old baseline. Cross-project and read-only authorization remain repository-enforced.

## Independent software checks and metrology

Each output part is one valid native solid. Declared output interiors may not overlap; contact is not an inferred weld/contact law. STEP preserves a separate-body compound. STL carries no assembly semantics; its verified per-part contiguous triangle-range inventory is retained separately.

Kernel-independent exact polynomial integrals supply volume, centroid and bounds. Each actual STL part is checked for closed/oriented topology and its correct Euler characteristic, including through holes and channels. Separate Gmsh STEP reimport measures every actual body/face and checks unique body and semantic-face correspondence against native construction-history witnesses. Ambiguous or missing matches fail. Gmsh and OCP share OCCT: this is independent process/import/API plus independent mathematical reference, **not independent kernels**.

Six distinct, explicit QA ceilings/source are required: relative volume, centroid, signed implicit constraint residual, reverse sampled surface distance, semantic relative area and semantic centroid. The Boolean constraint residual is **not a general Euclidean signed distance or Hausdorff bound**. Reverse checks use actual retained STL triangles/imported trimmed faces. No missing sample is replaced by a successful value. Coincident cutter end caps do not falsely qualify open channel-port interiors as retained metal surfaces.

Supported analytic local-X sections report source-bound annulus/sector/ellipse area and the actual frame-transformed plane. They are exact formulas for the admitted feature language, not arbitrary-plane kernel intersections, mesh-derived measurements or flow/structural acceptance. Actual native/reimport volume, area, centroid and bounds are shown separately. Viewport clipping/vertex picking remain display-only.

## Independent review and handoff

Unreviewed CAD downloads remain plainly labelled candidates. A different active authorized project engineer must explicitly attest source applicability, topology/dimensions, channels/ports/ligaments, named boundaries/interfaces, materials/mesh criteria and limitations. Review binds the exact current attempt/head, every actual artifact hash, reviewer identity and declared qualifications/intended use. Credentials are reviewer-declared, not externally certified. The build creator cannot self-review; posted acceptance/solver flags are not authority.

An accepted decision creates a derived published record **only for geometry-analysis preparation**. The original candidate is immutable. Named boundaries and paired metal/coolant interfaces bind exact STEP entities/revision. Material regions are explicit labels/sources, not solver property tables. Mesh constraints are explicit intent, not a generated volume mesh.

Study setup retains accepted STEP checksum, review identity, frames, material regions, named selections, interface pairings and mesh intent. It declares `mesh_status=NOT_GENERATED`, `execution_status=NOT_STARTED`, `solver_supported=false`, physical validation `NOT_PERFORMED`. New engine CFD/FEA/volume meshing belongs to R09. A remap is an unaccepted proposal with explicit heuristic confidence, never inherited acceptance; edits require a new independent review. Synthetic reviewer workflow tests do not constitute real sign-off.

## Bounds and qualification meaning

Contract admission: at most 24 features/frames/output parts; profiles 2–129 points; cooling 3–16 passages; plate patterns 3–24 ring positions; source/export tolerances explicit. Hard execution limits include 200,000 combined STL triangles, 5,000 native faces/part, separate bounded reader payloads/nodes, 120-second native/QA budgets, existing supervised process/RSS limits and 16 distinct cached QA profiles per application lifetime. Exceeding a bound produces a retained failure, not decimation, partial export, auto-coarsening or acceptance.

These are rejection ceilings, **not a promise that every combination at every maximum will succeed**. The qualified engine-derived workload uses all 81 divergent stations plus three upstream points, three internal channels, one metal and three fluid bodies, with explicit test-only 0.2 mm tessellation/0.4 mm sampled QA ceilings. The same source is tested in a proper rotated/translated frame. Smaller manufactured cases exercise every injector family. Intended-use tolerances and larger/other combinations must be evaluated explicitly; software success is not production/physical readiness.

Generic project backup/archive retains the new domains. Editable input cloning remains the existing scoped clone: it does not silently clone/rebind component models/reviews to a new baseline. Original archived evidence remains accessible.
