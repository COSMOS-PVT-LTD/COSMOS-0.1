# P03 shared scientific design system: implementation and G2 evidence

Date: 2026-10-08. Base SHA: `293223ebef190eaa647e67dc581eb186b2b5d987`. The checkout includes substantial pre-existing user work; this phase preserved it.

## Outcome and phase boundary

The opt-in scientific component foundation is implemented in `gui/static/design-system/`. All 18 specified components, a semantic token registry, typed consumer interfaces, unit/plot/status contracts, keyboard navigation, theme/contrast checks, two internal scripted task studies and visual baselines are delivered. **G2 PASS is limited to the tested library and laboratory.** This is not a claim that production-wide controls were migrated or certified. G3/P04 owns shell integration, compatibility and rollout/rollback.

The user's exact message, “execute p03 , i approve p01 and also complete p02”, is recorded as P01 owner acceptance. P02 completion is a separate bounded source-worker candidate with 21/21 accepted fixtures, explicit conditioning/refinement and preserved raw failures. Neither acceptance grants frozen-architecture deviations, production native integration or release approval.

## As-built reuse and architectural choices

| Existing file / symbol | Reuse or preservation decision |
|---|---|
| `gui/server.py:CosmosApplication`, `CosmosApplicationHandler` | Preserve Python HTTP framework. Use its actual routes in a scratch-data browser fixture only. |
| `gui/static/app.js:COSMOS.initWorkbenchDetail`, workbench catalog | Preserve all 12 actual workbench routes; derive the baseline list from the P01 verified catalog. No renamed/invented capability. |
| `gui/static/cosmos-tokens.css`, `cosmos.css`, `cosmos-shell.css` | Existing design vocabulary and compatibility reference. No edit; new CSS is `.cosmos-ds` scoped and opt-in. |
| `gui/static/engineering-ux.js` | Preserve real project context, commands, notifications, job polling and console. New shared components are presentation/intent primitives, not a duplicate backend or replacement service. |
| `gui/static/propulsion-suite.js` | Preserve all scientific request/result behavior. New UI does not call calculators or rewrite current parameter defaults. |
| P01 navigation/task/wireframe/model evidence | Reuse active-versus-inspected context, navigation names, truthful independent status and missing-evidence recovery. Production connection is future P04. |
| `tests/js/*.test.cjs`, `.venv-remediation`, existing GUI integration tests | Preserve test framework and dependency environment. Add focused tests; execute regression rather than substitute synthetic checks for scientific tests. |

No functioning module was removed, no React migration was introduced, and no architecture ADR was needed. The opt-in loading boundary is the rollout control: unless its assets and root class are mounted, the legacy UI remains unchanged. P04 must supply actual state adapters, workbench mount/unmount lifecycle, rollback switch and real job/export/review routes.

## Deliverables

`tokens.json` centrally defines dark/high-contrast semantic roles; generated `tokens.css` is drift checked. `components.css` has no copied color literals or network fonts. `components.js` exports the 18 components plus strict SI parsing, bounded windows, typed diagnostics and safe evidence links. `components.d.ts` describes public consumer contracts; this is not a claim that the JavaScript implementation received whole-program static type checking. `README.md` records integration and scientific limitations. `index.html`/`gallery.js` are labelled synthetic demonstration fixtures.

Unit inputs preserve invalid drafts and last accepted SI values. Repeated display switches preserve canonical SI exactly without emitting an edit. Trees/tables keep at most 20 rows/items in the DOM; the fixture uses 10,000 input entries. Plots require units, residual definitions and scale, retain numeric Y-axis values, explicitly label sampling and frame-throttle copied display snapshots. Scientific calculations, verification and validation are not inferred from these display operations.

## Executed checks

| Check | Result and evidence |
|---|---|
| Python repository regression | 2,234 passed, 5 skipped; `logs/pytest.log`, `logs/pytest.xml` |
| JavaScript repository regression | 57 passed, including 34 design-system tests; `logs/js-tests-final.log` |
| Real-browser component + legacy checks | 44 passed, zero retries; `browser-tests.json`, `logs/browser-regression-accepted.log` |
| Accessibility | Zero automated violations for dark and high-contrast WCAG-tagged/best-practice checks; raw reports retained |
| Contrast | Semantic text/status tokens at least 4.5:1 and focus rings at least 3:1 against all three surfaces in both themes |
| Keyboard/recovery | Tab/modal trap and Escape restore; tabs/tree, nested parent navigation, cancellation/review/export intents, split-dock persistence and reset |
| Scientific refusal paths | Invalid/missing/nonfinite values, unknown units/states, missing status evidence, unsafe URLs, log-zero data, invalid initial SI bounds, stale/failed export |
| Visualization | 100 updates coalesce to one frame; copied source survives caller mutation; 10,001-point input renders 1,000 points; disposed plots reject updates |
| Scaling | 200% text at 1024×768 with no horizontal document overflow; context remains visible |
| Visual regression | 18 component goldens, ten-state fixture, scaled view and all 12 workbench goldens; repeated comparison, not creation alone |
| Ruff | Repository targets plus new phase Python tools pass |
| Mypy | Existing configured scientific/API scope passes, 318 source files |
| TypeScript consumer declaration check | Strict declaration/consumer checks pass; no production TypeScript dependency added |
| Source preservation | All 1,599 checkpoint files unchanged except the four explicitly authorized P01/P02 records; added files confined to the allowed slice |

Five Python skips remain existing knowledge-source fixture skips, not evidence of physical validation. The baseline P00 count is preserved. No tests required changing core, physics, numerics, systems, API or legacy GUI implementation.

The existing global-cache unit test refreshed the tracked `cache/cea/test_key.json` fixture's creation timestamp. The scope checker caught it. Its pre-phase hash exactly matched both Git HEAD and index, so the original timestamp was restored with a targeted patch and the full checkpoint hash rechecked. The generated test version is retained as `cache-generated-after-tests.json`. No user-authored cache content was discarded or guessed.

## Screenshot calibration and reproducibility

First automated checks found an unfocusable table scroll region and a fixture selecting an input before the real Requirements module was opened. Both were fixed and retested. Initial legacy captures raced asynchronous data/art decoding and transient startup toasts; fixtures now wait for loading/fonts/image decode and hide only startup toast/animations/canvas while masking timestamp/log content. No application source was modified to obtain snapshots.

After settling, exact legacy comparisons still found isolated antialiasing differences. `legacy-rasterization-calibration.json` and the retained actual PNG record 38 raw changed pixels, maximum channel difference 12 and a measured pixelmatch YIQ bound of 0.0424516095, rounded up to **0.0425**. Only legacy tests use that color threshold, with **zero differing-pixel allowance**. New component tests use threshold **0** and zero differing-pixel allowance. This is visual-test calibration, not a scientific tolerance change. Failed runs remain under `logs/` so the decision history is inspectable.

The final run uses installed Chrome 154.0.8037.98 on arm64 macOS 26.5.2, viewport 1440×1000, DPR 1, reduced motion, one worker, fresh isolated browser contexts and no retries. Baselines are platform-specific, as explained in the [Playwright snapshot documentation](https://playwright.dev/docs/test-snapshots). Legacy external font/network requests are blocked, so they represent deterministic offline local-font views. Canvas imagery and transient logging are not covered by those screenshots; this is a shell/route visual baseline, not visualization correctness evidence.

## Interaction baseline and limitations

`interaction-performance.json` records 50 synchronous input-handler dispatches and JavaScript heap size with 10,000-row/tree fixtures. `legacy-interaction-baseline.json` records the corresponding real Requirements input in the isolated original app. P03 produced no unrelated plot/table mutations. `PERFORMANCE_BUDGET.json` derives the handler budget from the observed legacy maximum and records the measured heap baseline; it is explicitly scoped to this fixture and device. Timer quantization, browser GC, synthetic events, paint latency, full-app overhead and native RSS prevent interpreting these observations as production SLAs.

The tests follow [WCAG text-contrast guidance](https://www.w3.org/WAI/WCAG22/Understanding/contrast-minimum.html) and [modal keyboard guidance](https://www.w3.org/WAI/ARIA/apg/patterns/dialog-modal/). Automated accessibility and scripted internal tasks do not certify WCAG conformance, a native screen reader, actual-user usability or cross-platform desktop behavior. VoiceOver/native-wrapper/manual review remains a later release acceptance item.

## P04 readiness and remaining gates

**Ready to start P04, not executed here.** Mount the library behind a recoverable shell rollout boundary. Connect P01 navigation and real context/state through existing application services. Preserve all 12 routes and scientific API contracts; use original arrays/artifacts for scientific evidence, not sampled plots. Rerun compatibility, state and numerical parity checks after integration.

Remaining release risks are native geometry packaging/platform/SBOM closure, manual assistive-technology and real-user acceptance, and real state/job/signoff/export adapter integration. No commit, push, PR, merge, production data mutation or CI/CD claim was made in this phase.
