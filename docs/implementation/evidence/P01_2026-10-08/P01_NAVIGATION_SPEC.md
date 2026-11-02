# P01 — Navigation and experience architecture

Status: proposed for owner review; not production routing. Date: 2026-10-08. Baseline HEAD: `293223ebef190eaa647e67dc581eb186b2b5d987` plus the preserved P00 working-source fingerprint.

## Outcome

Make the engineering task—not a module list—the primary navigation model. Keep project/design/revision identity and scientific state visible. Retain all working calculations, existing routes and Knowledge governance. Clearly distinguish currently available functionality from proposed geometry, simulation and V&V.

The [interactive wireframe](prototype/index.html) is synthetic and isolated. [navigation.json](navigation.json) is a proposal/test fixture, not a configuration imported by the production server.

## Primary destinations

| Destination | User task | Current maturity | Proposed ownership |
|---|---|---|---|
| Projects & Mission Workspace | Open/create context, select design, inspect requirements/revisions, recover layout | A design store and browser context preference exist; authoritative project service is proposed | P04 shell; revision/publication contract coordinated with P06 |
| Rocket Engine | Define requirements/model/operating point; preflight; calculate; size supported subsystems; inspect/review/export | Active, scientifically partial | P05; existing API/Systems/Physics/Numerics remain scientific owners |
| Native Geometry Generator | Build accepted representation-aware geometry from a published snapshot | Planned; no registered NGG/kernel | P06–P08 |
| Simulation | Accepted geometry → selections/materials/mesh → study → monitor → results | Planned; current route is a descriptive detail page | P09 |
| Comparison & V&V | Align independent data and quantify error/uncertainty | Planned; not equivalent to Code Comparison | P10 |
| Maharshi Bharadwaj Knowledge | Inspect sources/equations/applicability/review; disclose missing evidence | Active workspace | P11 presentation over existing Knowledge services |
| Reports, History & Governance | Trace input/method/artifact/run/evidence; review and publish report | Some design export/change logs exist; full lineage/report service proposed | P04/P11; immutable artifact contract from P06 |

The navigation label is not permission to run a capability. Future production controls use a capability manifest with maturity, backend availability, model limits, permission and prerequisites. Planned pages must repeat maturity on direct entry, not only on the hub.

## Context hierarchy and vocabulary

- **Project:** durable engineering workspace identity and permissions. Current localStorage project name is only a UI preference, not that identity.
- **Design:** an editable engineering aggregate within the project, with a stable design ID.
- **Draft:** unsaved working edits. It must survive workbench switches and not alter a published snapshot.
- **Revision/snapshot:** an immutable published input/configuration record, addressed by revision ID and hash. Current change-log increments alone do not provide this.
- **Artifact:** a generated immutable geometry/mesh/result/export record with representation, units, frame, source snapshot and hashes.
- **Study:** declared model, mesh/material/boundary/settings configuration.
- **Run:** execution against a fixed snapshot, with event history and result identity.
- **Verification:** analytic/code/solution or independent-reference evidence, with scope and disposition.
- **Validation:** comparison against qualified experimental evidence; never inferred from execution success.
- **Stale:** dependencies have changed relative to an artifact/run's original source. Original inputs/evidence remain readable.

Header shows project → design → active draft/base revision. Read-only inspection of another revision is additionally labeled “Inspecting rN”; it does not replace the active base or draft. If the underlying immutable revision service is unavailable, the production UI must say so. Never fabricate a working revision checkout from a change-log counter.

## Global shell contract

Persistent context, workbench navigation, breadcrumbs, display-unit preference, truthful run queue, notifications, command palette, help and source links. Prototype uses SI only; it does not implement a conversion system.

Left: primary workbenches and contextual project/feature tree. Center: editor or viewport for the current task. Right: contextual properties, assumptions, evidence and input-snapshot inspector. Bottom: diagnostics, job/history/events. Panels are collapsible, resizable and recoverable to defaults; UI layout preferences are stored separately from scientific records.

At the native minimum 1100×700, collapse supporting panels before sacrificing critical labels, actions or active context. Avoid two parallel stage-navigation rails and redundant project indicators. Large tables/trees are virtualized in later implementation, not fabricated performance-qualified here.

On navigation, retain drafts, selected result and scoped context; focus the new task heading/editor and announce the destination. On inspection, preserve the editor and announce the inspected snapshot. On missing-input recovery, focus the exact field. On modal dismissal, restore a connected invoking control or a defined command-button fallback.

## Rocket task architecture

Group the 17 existing stage IDs without changing their DAG, execution order or scientific maturity:

| Group | Existing stage IDs |
|---|---|
| Define | `design_project`, `requirements`, `propellants`, `cycle`, `operating_point` |
| Calculate | `thermochemistry`, `performance` |
| Size subsystems | `injector`, `chamber`, `thermal`, `cooling`, `nozzle`, `structure`, `materials` |
| Review & export | `performance_summary`, `consistency`, `design_review` |

Preserve individual stage links and the existing physics tools. Groups improve discoverability; they do not introduce new computation ownership. Cycle remains unsupported and preliminary bypass stays explicit.

Active task shows required inputs and model selection, input readiness, draft/base identity and dependency impact before a run. Missing is not zero. Blank ambient pressure produces a field-linked preflight issue; explicit 0 Pa means the user selected vacuum. Applicability checks belong to Physics; UI input presence checks are not a second physics model.

Result hierarchy: concise quantities with units → independent execution/termination/physical/verification/validation status → station/profile data → assumptions/limits → source and exact input snapshot → export eligibility. Keep raw machine-readable detail available in Expert mode. Never turn a failed/out-of-range result into a green success because another stage completed.

## Guided / Standard / Expert

These are presentation modes, not solver profiles. All modes expose critical units, explicit required inputs, unsupported capability notices, failures, stale state, model limits and validation status.

- Guided: task order, explanatory help, prerequisite checklist and field-linked recovery.
- Standard: normal task controls, compact result/assumption/evidence inspection.
- Expert: denser parameter tables, raw contracts, provenance/history and advanced inspection, without bypassing checks.

Changing mode must leave numeric parameters, selected models, boundary conditions, tolerance policy and published IDs unchanged. Density preferences may persist as UI preferences. No hidden “fast”, “accurate” or geometry-resolution default is attached to a mode.

## Compatibility catalog and route policy

[navigation.json](navigation.json) retains all 12 audited workbench IDs and exact routes. Rocket/Knowledge map to the primary destinations; Simulation maps to its honest planned page. Turbopumps, PID, Structures, Rocket Staging, Manufacturing, Visualization, Documentation, Code Comparison and PLM remain in an “All workbenches” catalog with current maturity. Do not remove or silently redirect them to a scientifically different feature.

Production routes `/app/workbench/rocket-engine` and `/app/workbench/knowledge` remain canonical in the first migration. Preserve Rocket `stage`/`module` query context and the legacy compressible-flow redirect. Proposed project/NGG/V&V/report routes must be resolved in P04 contracts rather than invented as live endpoints during P01. Browser back/forward and unsaved-state behavior need route tests before integration.

## Status and action policy

No single green “success” badge summarizes all scientific dimensions. Display draft/freshness, execution, numerical termination/convergence, physical admissibility/conservation, verification and experimental validation independently. “Review accepted” includes the reviewer, scope, record and date; it is not an assumed permission or certification.

Unsupported actions remain disabled with an adjacent explanation and recovery/prerequisite link. An unavailable geometry kernel or reference dataset cannot yield a publishable artifact. Client timeout ≠ cancelled worker; cancellation stays requested until backend acknowledgement. Source absence is explicitly `INSUFFICIENT_EVIDENCE`.

## Review boundary

Owner approval confirms this navigation/task architecture only. It does not approve a frozen package move, framework replacement, scientific-default change, security exposure, kernel license or release. See [review record](P01_REVIEW_RECORD.md) and [migration seams](P01_MIGRATION_SEAMS.md).
