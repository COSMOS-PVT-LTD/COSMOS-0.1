# P01 — Scope and file-scoped execution plan

Date: 2026-10-08. Phase: `P01_EXPERIENCE_ARCHITECTURE`.

Authority: modernization pack P01 prompt, platform UX, governance, workbench specifications and G1. Entry evidence: [P00 audit](../P00_2026-10-08/P00_AUDIT_REPORT.md) and [G0 decision](../P00_2026-10-08/G0_DECISION.json).

## Scope

Produce persona tasks, navigation specification, engineering journey maps, wireframes, an isolated interactive workflow prototype, accessibility plan, migration seams and a review/approval record. The prototype is not a production shell or geometry/solver implementation. No actual project records, native solver, credentials or uploads are accessed.

## Plan

1. Recheck HEAD and P00 source hashes. Capture the current nonignored working source before changes.
2. Define seven primary destinations and retain every existing workbench/deep link in the compatibility catalog. Distinguish active, partial and planned capabilities.
3. Define personas and critical task flows, including missing inputs, stale/conflicting revisions, cancellation, failed QA and absent source evidence.
4. Build a separately served structural prototype inside this evidence directory. Reuse the current dark workstation vocabulary, unit labels, status dimensions and command/navigation concepts. Do not perform a visual redesign or add a framework/runtime dependency.
5. Add isolated state-model tests. Verify browser task flows, keyboard focus, minimum viewport, mode invariants and layout recovery. Capture screenshots and concise evidence.
6. Record automated design review separately from human acceptance. Keep G1 pending if the owner has not reviewed the deliverables. Do not start P03 production design-system work without acceptance.

## File boundary

Only `docs/implementation/evidence/P01_2026-10-08/` may be added/edited. Planned artifacts: navigation/task-flow/wireframe/accessibility/migration Markdown; navigation JSON; prototype HTML/CSS/JS and state-model tests; source-preservation/evidence helper; screenshots; phase and approval records.

## Reuse and conflicts

- Reuse `gui/workbenches/registry.py`, `gui/workbenches/propulsion_suite.py`, `api/catalogs.py` and the P00 workbench/stage inventories as capability truth, not registry marketing descriptions as proof.
- Retain `gui/static/engineering-ux.js` command/context patterns and `propulsion-suite.js` unit/error/freshness semantics. This prototype does not edit or import their runtime.
- Leave Core, Numerics, Physics, CEA, Systems and API ownership unchanged. Current `systems/` versus frozen `engineering/` naming needs a future approved ADR, not a P01 relocation.
- Immutable historical snapshots, geometry jobs and revision CAS are demonstrated only in synthetic in-memory scenarios. They are not present production capabilities. Implementation remains P04/P06/P07.
- The Product Design context workflow grounds the task-first prototype in P00 screenshots and source. A Codex Canvas is not used because the requested deliverables are a repository-specific P01 package and runnable workflow prototype.

## Gate policy

G1 requires navigation flows, prototypes and review record. Automated checks can establish prototype consistency, not owner approval or a user study. The approval record must remain `PENDING_OWNER_REVIEW` until explicit acceptance is supplied. P02 remains independently eligible after G0; it is not executed as part of P01.
