# R07 broader component/editor/handoff execution

User authorization: extend beyond the divergent nozzle to combustion chamber/convergent/throat, injector families and internal regenerative channels, reversible component editing and study handoff. Preserve frozen layers and all functioning fixture/nozzle modules. Baseline `293223ebef190eaa647e67dc581eb186b2b5d987`, inherited dirty tree; preceding source inventory `R07_NATIVE_INTEGRATION_2026-10-20/source-final.json`.

## Finite geometry profile

1. Typed geometry features over existing P06 snapshots/graphs/frames: axisymmetric profile walls/solids, real plate drilling, internal contour-following axial sector passages, proper rigid placements. No GUI CAD equations. Explicit SI dimensions, source/export tolerances, source/applicability, dependency/output selection and immutable revisions.
2. Templates: full chamber/convergent/throat/divergent profile from exact saved chamber/nozzle data plus explicitly supplied missing dimensions; showerhead and impinging-doublet/triplet drilled plates; shear-coaxial tube assemblies; continuous-gap pintle assembly. Geometry only; no inferred atomization, swirl stability, pressure losses or propellant allocation. Unsupported swirl/helical/manifold variants fail explicitly, not mislabeled generic holes.
3. New versioned component policy/worker, preserving old fixed-fixture and divergent-nozzle validators. Native one-solid checks per declared part; named multi-body assemblies retained as such, no accidental fusion or overlap. Source B-rep and metre STEP/STL with source/export/semantic identities.
4. Independent per-part analytic volume/centroid/bounds and actual mesh topology, sampled surfaces, CAD reimport/placements and critical dimensions. Internal passages must be actually subtracted from the metal. Multi-body STL needs an explicitly verified part-range map; STL does not encode CAD hierarchy.
5. Reuse R05 managed revisions, CAS, commands/history, durable attempt/stage/blob/coordinator/supervisor. Add reversible feature edits and graph impact; preserve unknown/invalid/cyclic diagnostics, exact selected results and upstream freshness.
6. Native Geometry workbench project editor with feature tree/parameter inspector, placement and dependency controls, undo/redo/restore via immutable commits, real previews and source-bound QA/downloads. No silent engineering defaults or fake completed geometry.
7. Revision-bound named selections/material regions/interface and mesh-constraint setup. Independent active project engineer review must bind exact bytes, methods, declared use and criteria before engineering publication/handoff. Do not invent a signature. Explicit remapping after edits; ambiguity/staleness blocks handoff.
8. Component study **setup/handoff**, separate from the existing sphere-only solver. New engine CFD/FEA/meshing is R09 scope and must remain unsupported here. A handed-off setup is not an executed or validated simulation.
9. Qualify positive/negative analytic/native/API/access/history/undo/cancel/recovery/selection/review/handoff/browser paths; re-run preserved fixtures/nozzle and full regressions/static/JS checks. Native runtime/config receipts are new campaigns, never rewrites of historical evidence. Protect the CEA cache and owner roots.

## Acceptance boundary

The code/workflow can be completed and qualified using manufactured test geometry and distinct synthetic reviewer accounts. Actual intended-use acceptance, manufacturing/hardware readiness and physical validation remain pending authentic owner evidence/review, not automatically satisfied by implementation. Any unsupported numerical or manufacturing feature remains explicitly outside the declared V1 profile.
