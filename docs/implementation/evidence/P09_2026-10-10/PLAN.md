# P09 simulation implementation plan

Baseline: HEAD `293223ebef190eaa647e67dc581eb186b2b5d987` plus preserved dirty working tree. P08 seal verified before changes: 2,921 files, G5/G6 software PASS; human acceptance and production native publication remain false.

## File-scoped vertical slice

1. Preserve baseline source hashes and original files before modifications. Capture the existing planned Simulation screen.
2. Add `numerics/finite_volume/radial_diffusion.py`: bounded spherical control volumes and iterative diffusion balance. Reuse existing `diffusion.flux`; do not change existing numerical defaults or equations.
3. Add `physics/heat_transfer/spherical_conduction.py`: isolated constant-conductivity, uniform-generation steady spherical benchmark. Independent analytic solution and mesh refinement establish software solution verification, not experimental validation.
4. Add `simulation/`: immutable study/handoff/mesh/run records and bounded asynchronous actor-scoped service. Consume existing P06 NamedSelection and P08 accepted candidate, exact snapshot, graph, source/export byte hashes, independent QA. Only OCCT sphere software candidates qualify. No arbitrary file import, general CFD/FEA, engineering publication or remapping inference.
5. Add `api/simulation_workbench.py`, thin `gui/simulation_ui.py`, and additive `gui/server.py` routes. Strict default-off `COSMOS_NEW_SIM_UI`; loopback/authentication/roles, bounded request bodies and exact field checking. Existing DesignStore is not mutated.
6. Add `gui/static/simulation/` and workbench page. Reuse design-system PlotPanel, Legend, ParameterTable, ProjectTree, JobMonitor, ErrorDetails, and existing resizable shell. Study/mesh/settings/monitor/field inspection with SI labels, separate numerical termination/conservation/admissibility/verification/validation dimensions. Reversible local draft undo, no numerical algorithms in GUI.
7. Add independent analytic/refinement/negative/cancellation/corruption/stale/transport/plot tests and real authenticated browser flow using actual OCCT generation and independent STEP QA. Record screenshots, accessibility and target-Mac timings, physics parity and full regression summaries.

## Dependency and authority

G5/G6 software receipts -> real accepted sphere + exact semantic outer surface -> immutable radial FV mesh -> study snapshot -> bounded queued run -> residual/conservation events -> immutable dataset -> source-linked plots -> G7 software assessment.

The frozen architecture explicitly contains Simulation, Physics, Numerics and API. This adds the first working `simulation/` slice, not a replacement subsystem or storage ownership change. Geometry remains owned by the existing Systems service; Simulation consumes immutable accepted software candidate DTOs. GUI consumes API only. This fixture handoff is not the GOV-005 independently reviewed **engineering** handoff: production handoff must remain refused until engineering acceptance/publication exists. No new dependencies, native upgrades or existing physics changes are planned. P10 is not executed.
