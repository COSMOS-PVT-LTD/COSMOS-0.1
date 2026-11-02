# P10 changes — 2026-10-11

- Add a default-off Comparison/V&V workbench in the frozen `validation/` area. Keep the legacy Code Comparison workbench and all prior science modules.
- Add exact thermal import, immutable criteria/receipts, explicit units and coordinate/condition checks, independent analytic comparison, discrepancy metrics and conditional reported-output uncertainty. Block inferred transforms, hidden interpolation, self-comparison, late criteria and forged acceptance.
- Reuse accepted OCCT/PicoGK QA and the qualified bounded Gmsh reader for fixed-fixture cross-kernel comparisons and trusted sphere STEP import. Record shared-kernel versus distinct-kernel limits.
- Reuse shell/themes/shared components. Add criteria draft undo/redo, scientific plots, history, review intent, actionable errors, responsive focus layout and downloadable receipts.
- Preserve exact canonical receipt bytes across browser JSON serialization and reject tampering before rendering/export.
- Extend existing CI lint/type scope; run local Python, real native, JavaScript, display-contract, browser, accessibility, parity and refinement checks. Do not claim remote CI execution.
- Prepare the first physical-validation evidence/owner plan. No compatible measured dataset, qualified independent acceptance, production release, hot-fire readiness or flight readiness has been established.

Initial failed test/collection logs remain available. Final gate acceptance uses explicitly named final successful artifacts. This execution does not commit, push, merge, start P11 or rewrite predecessor gates.
