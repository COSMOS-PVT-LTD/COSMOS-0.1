# COSMOS scientific design system — P03

This is an opt-in component library for the current vanilla-JavaScript DOM frontend. It does not migrate the framework, replace workbenches, or alter Python scientific code. Production shell adoption is **P04**, not this phase. The standalone laboratory is synthetic and performs no scientific API calls, job submission, real signoff or file export.

## Load and use

Load `tokens.css`, `components.css` and `components.js`, then mount components within a `.cosmos-ds` ancestor. Set `data-theme="dark"` or `data-theme="high-contrast"` on that ancestor. Avoid nesting theme roots unless all roots receive the same selected theme. The UMD library also supports CommonJS for pure-function tests. `components.d.ts` defines the public TypeScript consumer contracts without introducing a TypeScript build dependency into COSMOS.

```js
const field = CosmosDS.UnitInput({
  label: 'Chamber pressure Pc', dimension: 'pressure', unit: 'MPa',
  valueSI: 500000, minSI: 0,
  onChange: quantity => console.log(quantity.valueSI) // Pa; connect a draft adapter in P04
});
document.querySelector('.cosmos-ds').append(field);
```

The example is a display/draft boundary, not a new Physics implementation or a published calculation. Never attach it directly to a mutable published result.

## Tokens and text

`tokens.json` is the only semantic registry. It contains 13 color roles per theme, four text roles, spacing, control height and radius. `build_tokens.py` generates scoped CSS; run it with `--check` in validation to detect drift. Component CSS consumes semantic roles rather than repeating colors. UI text uses system fonts; measurements use tabular monospace numerals. No remote font download or licensed font payload is added. Greek/Unicode coverage follows the target system font fallback, not a universal-font certification.

Font scaling changes root `rem` size, not SI storage or solver settings. The laboratory exposes 100/125/150/200% controls. Reduced-motion and forced-color focus rules are included. Visible state text, dashed borders, disabled controls and error messages supplement colors. Modal dialogs trap Tab/Shift+Tab, support Escape and return focus. Keyboard instructions remain available through the component labels and docs.

## Public component contracts

| Component | Contract and boundary |
|---|---|
| `CosmosShell` | Shows project, active revision and inspected revision separately; accepts existing DOM content. No route or backend ownership. |
| `WorkbenchTabs` | Unique IDs, roving focus; Left/Right/Home/End. Emits navigation intent only. |
| `ProjectTree` | Bounded 20-item DOM window, sibling positions/size and level metadata. Up/Down/Home/End, expand, child and parent navigation. Emits inspection intent. |
| `PropertyInspector` | Composes labelled unit fields; does not edit published artifacts. |
| `UnitInput` | Strict finite decimal parsing; Pa/kPa/MPa, m/mm/cm, K and dimensionless display units. Explicit SI min/max. Blank is missing, not zero. Invalid text is retained; the last accepted SI value remains unchanged. Display switching does not emit a scientific edit or round-trip the canonical value. |
| `ParameterTable` | Explicit units/provenance, finite numerical values, 20-row window and accessible paging/scroll region. Rows remain in caller storage; this is DOM virtualization, not a lazy data backend. |
| `EngineeringStatus` | Separate execution, numerical termination, freshness, verification and validation. Verified/validated states require evidence links. It presents caller-reviewed status; it does not authenticate or assess that evidence. |
| `JobMonitor` | Explicit execution state, bounded fractional or indeterminate progress, cancellation-request callback. An intent is not cancellation acknowledgement. |
| `EvidenceLink` | Text-safe DOM; only local/hash/HTTP(S) links, no executable URL scheme. Evidence access permissions remain a backend responsibility. |
| `PlotPanel` | Quantity/unit on both axes. Linear/log declaration; residual definition mandatory. Rejects nonfinite or nonpositive log data. Numeric Y ticks remain in original units. |
| `Legend` | Quantity, finite ordered range, units, clipping and named color map. Text supplements colors. |
| `ArtifactBrowser` | Representation, status, SHA-256 and inspectable evidence. Does not fabricate provenance or readiness. |
| `SplitDock` | Pointer or keyboard resize, collapse, restore defaults. Persists only layout width/collapse; corrupt/unavailable storage recovers to defaults. |
| `CommandPalette` | Search, Ctrl/Cmd+K, trapped modal focus and disabled unsupported commands. Call `dispose()` to remove its global hotkey when unmounting. |
| `ErrorDetails` | Typed code, message, correlation ID and recovery guidance; expandable native details. |
| `ReviewSignoff` | Explicit evidence-review checkbox and immutable review **intent**. No certificate, identity check or physical-validation authority. |
| `ExportWizard` | Requires passed geometry QA, current freshness and a SHA-256 reference, then explicit acknowledgement. Emits exploratory STL intent with `cadReady:false`; no publishing/export API implementation. |
| `EmptyState` | States missing capability/evidence and an optional explicit recovery action. Missing callbacks disable the action. |

Errors use `DesignSystemError` codes and structured `diagnostic()` results. Host adapters should catch these at their boundaries and route them to `ErrorDetails`; do not replace failures with plausible results. General visual states are enumerated in `states` and applied with `applyState`; native controls retain their own disabled/invalid semantics.

## Visualization and performance

`PlotPanel.updatePoints(points)` copies the display snapshot and coalesces repeated updates to the latest snapshot once per animation frame. `dispose()` cancels pending redraws. Rendering is bounded to 1,000 uniformly sampled, endpoint-preserving points. The caption explicitly states that sampling is **not extrema-preserving**. This display optimization cannot be used for acceptance metrics, peak analysis, convergence evidence or scientific downsampling. Those require original numerical data and a separately reviewed algorithm. Unit edits do not redraw unrelated plots, tables or the shell.

Tables and trees bound DOM nodes but keep their input arrays in memory. Do not infer arbitrarily large-dataset scalability from the 10,000-entry fixture. Local handler timings and JavaScript heap observations are in the P03 evidence folder; these are measured development baselines, not end-to-end latency, native memory, or production SLAs.

## Test and preview

```sh
.venv-remediation/bin/python gui/static/design-system/build_tokens.py --check
node --test tests/js/design_system.test.cjs
python3 -m http.server 8793 --bind 127.0.0.1 --directory .
```

Open `http://127.0.0.1:8793/gui/static/design-system/`. Browser-tool setup, isolated legacy-server commands, evidence and P04 integration seams are documented in `docs/implementation/evidence/P03_2026-10-08/`. Do not point the test fixture at the user's live project data.
