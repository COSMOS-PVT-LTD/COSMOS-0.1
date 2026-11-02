# Guided Design — first development delivery

Date: 2026-10-29. User approval covers GD-00 through GD-06. This delivery is a
working preliminary slice, not a claim that all seven work packages are complete.
The frozen architecture, old app, saved baselines and historical runtime receipts
are preserved. Full engine generation and R08 remain ON_HOLD.

## What works now

- Guided Design is the normal Rocket Engine entry. Six primary decisions:
  thrust, propellant pair, absolute chamber pressure, environment, duration (or
  explicit steady-only scope) and cycle. Detailed existing editors remain in
  Expert Mode; the guided result links to the exact ordinary propulsion object.
- The initial guided profile is methalox / pressure-fed / ideal CEA target sizing.
  It proposes explicit cryogenic inlet assumptions, chamber/contour settings and
  cold injector/feed screening choices. No physical meaning is assigned to a
  hidden numeric default. The user reviews and accepts the exact basis first.
- Offline NIST cold reference states are original-byte and SHA256 checked.
  Their exact species, temperature, pressure, liquid phase and reference state
  are retained. Uncertainty remains unknown, not zero. The initial profile's
  inlet temperatures are fixed to the covered named states; no implicit hot
  properties, interpolation, phase prediction or alternative source is supplied.
- CEA resolves gas state; a bounded coarse/refined O/F study selects maximum
  modelled ideal Isp at the declared ambient. Sea-level/custom cases use matched
  exit pressure unless explicitly locked. Vacuum uses a reviewed finite expansion
  cap. Boundary optima and conflicting throat/target locks fail explicitly.
- Throat sizing, flows, chamber sizing and tangent-bell contour use existing
  Physics/Systems services. At the exact 5 bar + 1 bar injector-drop reference,
  cold hydraulic injector sizing is populated automatically. Other unmatched
  cold-manifold states block that assessment without discarding ideal performance.
- Regulated-feed screening reports pressure remaining after chamber and injector
  drop. This is NOT a full line/valve/cooling loss budget or operating-point solve.
- Accepted inputs are persisted before native computation. A bounded supervised
  process runs the study; queued/running/failed/cancelled/interrupted/completed
  states and exact operation identities are retained. Cancellation does not
  substitute or publish a successful result. Application close cancels owned work.
- Every successful run appends a normal managed propulsion design and retains
  its accepted-source dependency. Existing designs are not overwritten. Sources,
  methods, overrides and the review hash remain inspectable after reopen/export.
- Guided UI hides irrelevant legacy 'No inspected design / No jobs' chrome,
  exposes the actual guided status, uses progressive disclosure, maintains a
  visible step indicator and moves to results when calculation completes.
- Existing project component CAD appears directly on the engine page. Opening
  its retained preview does not regenerate it. PicoGK display bytes are SHA256
  checked; analytic OCCT and implicit PicoGK are labelled separately. A model is
  only labelled matched when its exact physics commit matches the selected run.
  Another project's/root's geometry is never silently borrowed or rebound.

## Initial numerical acceptance case

Isolated software case only: 1,500 N target, 500,000 Pa absolute chamber pressure,
standard sea-level pressure, LCH4/LOX, 5 s and pressure-fed. Reviewed nominal
inlet assumptions: methane 111.15 K, oxygen 90.15 K.

- Selected finite-grid O/F: approximately 2.63.
- Ideal calculated thrust: approximately 1,500 N, within the predeclared relative
  tolerance 0.0002 (this is a software target check, not a hardware tolerance).
- Ideal Isp: approximately 202.51 s.
- Ideal total flow: approximately 0.75532 kg/s.
- Cold injector evaluation available at the exact retained reference state.
- Matched cooling, heated feed, cooled-wall/joint readiness and physical
  validation remain explicitly BLOCKED / NOT_PERFORMED.

These numbers do not establish delivered thrust, combustion efficiency,
stability, thermal adequacy, pressure-joint qualification or manufacturing use.

## Implementation map

- systems/guided_engine/resolution.py: brief validation, units, applicability,
  profile rules, original/override trace and exact review hash.
- systems/guided_engine/evaluate.py: bounded study and existing-model orchestration.
- plugins/guided_engine/sources.py and data/: pinned offline cold reference pack.
- plugins/guided_engine/worker.py: one bounded stdin request; no arbitrary commands.
- systems/projects/guided_engine.py: accepted input authority, durable attempts,
  supervision callbacks, source stability, cancellation and normal-design handoff.
- api/guided_engine.py: authorized routes, source composition and trusted worker
  argv/environment; no numerical equations in the GUI/API.
- api/project_authority.py: lazy, locked guided composition and lifecycle cleanup.
- gui/static/guided-engine.js and .css: scoped guided experience and retained CAD.
- gui/static/workbench/rocket-engine.html and gui/server.py: existing route/asset
  integration; no replacement of functioning workbenches.
- scripts/build_standalone_desktop.py: optional distinct development identity.
- scripts/refresh_unqualified_desktop_sources.py: refuses existing verified apps.
- scripts/qualify_desktop_bundle.py: absolute reference paths and safe resume of
  a still-unqualified task stage, preserving failed reports.
- scripts/finalize_guided_desktop.py: explicit evidence checks, local signature
  and a new Desktop shortcut; never replaces the existing app/icon.

## Executed verification

The verification skill traced brief -> UI review -> authenticated API -> retained
inputs -> supervised CEA -> saved propulsion result -> native display -> Expert
Mode -> reopened history. Native test data are isolated, not user measurements.

- Source environment: 119 selected Python tests passed (34 guided/packaging,
  84 compatibility and 1 small native saved-CAD discovery test).
- Bundled environment: 173 Python tests passed (139 native OCCT/PicoGK software
  cases plus 34 guided/packaging cases). These overlap the source environment;
  the counts must not be added as unique test coverage.
- Existing JavaScript regression: 35 tests passed. New guided interactions were
  exercised in real Cocoa/WebKit, not only syntax/static checks.
- Native menu smoke: all 8 existing routes rendered; WebGL2 available.
- Actual bundled guided smoke: six-decision case, exact review, run, saved result,
  Expert handoff and reopened history passed.
- Compiled launcher --check: primary imports and the NEW path-bound OCCT/PicoGK
  profiles passed without opening user data.
- Static audit: 1,037 Mach-O files checked; no external non-system absolute load
  dependencies. Scoped Ruff and JavaScript syntax checks passed.
- New application ad-hoc signature verified. No Developer ID/notarization,
  public release, remote CI, commit or push is claimed.

Visual evidence: `02-guided-six-input-workflow.png` shows the final source-native
six-input workflow in an isolated software case; `03-installed-development-app.png`
shows the separately sealed application after cold launch. The final source-native
capture also completed the supervised CEA / saved-design / Expert / reopen flow.
The before-fix image is retained for traceability, not presented as final UI proof.

The first large-preview qualification invocation had a relative evidence-path
error after changing to the bundle directory. It did not indicate geometric
fidelity failure. The helper now resolves source paths before execution. Failed
report/log files were retained as pico-preview.failed-1.*; the corrected campaign
reused explicitly completed stages and executed the failed stage again. Only
the selected passing reports are counted in STATUS.json.

Bundled mixed-directory guided test collection initially lacked the checkout's
pytest.ini import mode. It was rerun with explicit --import-mode=importlib;
no user caches/data were deleted. The selected passing report is
output/guided-bundled-source-ready-2026-10-29.xml, not the failed collection log.

## Desktop handoff

New private app: /Users/vaibhavkumarn/Applications/COSMOS Guided Development.app.
New shortcut: /Users/vaibhavkumarn/Desktop/COSMOS Guided Development.app.
The existing COSMOS Desktop.app and its shortcut remain unchanged.

The new app was cold-launched after sealing and is left at its native workspace
chooser. Choose the existing folder, sign in, then Engineering -> Rocket Engine.
Main workspace contains existing calculations; Engine CAD contains the retained
component models. These roots remain separate. New guided calculations create
new designs, not replacement old engine baselines.

The new app is a separately qualified self-contained snapshot for this Mac/path,
not a live link to later checkout edits. Full engine generation and R08 remain
paused. A second app copy uses additional storage; no existing files were removed.

## Remaining work — approval is recorded, completion is not

- GD-03: broader reviewed fluid/inlet property coverage; constrained injector and
  cooling candidate search; matched hot-fluid/coolant/wall/material/feed closure;
  actual supplied-feed operating evaluation versus target sizing. Missing material
  allowables, supplier seals and physical data are not invented to clear a gate.
- GD-04: full advanced Expert-to-Guided override reconciliation and usability
  refinement beyond the initial six-decision workflow.
- GD-05: generation of the redesigned full engine and broader component/drawing
  acceptance remain under the explicit generation/R08 hold. Opening retained
  geometry is available and does not require resuming those operations.
- GD-06: genuine human task observations and acceptance remain pending. See
  HUMAN_TASKS.md. Automated execution is not a substitute for those observations.

The governing machine-readable receipt is STATUS.json. The original proposal
remains a historical planning artifact, not an assertion of current completion.
