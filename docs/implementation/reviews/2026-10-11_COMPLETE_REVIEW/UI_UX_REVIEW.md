# COSMOS 0.1 — live UI/UX review

Audit started 2026-10-11 and completed 2026-10-12, Asia/Kolkata. This folder retains its start date. Checkout: `/Users/vaibhavkumarn/Desktop/COSMOS/COSMOS_0.1`; committed HEAD `293223ebef190eaa647e67dc581eb186b2b5d987`, with pre-existing uncommitted modernization changes.

## Decision and method

**Functional research-preview interfaces exist, but whole-product UI/UX is not complete.** The strongest qualities are explicit units, provenance, unsupported-state labels, scientific acceptance restraint and real native/software operations. The largest problems are inconsistent navigation/context, crowded chrome, raw-text-heavy output, broken packaged uploads, incomplete cross-workbench engineering integration and nondurable modern history.

The Product Design audit skill shaped this review: fresh screenshots first, actual control interactions, exact saved-image inspection, strengths and risks tied to visible evidence. These are not reused P12 screenshots. No redesign or production fix was made. The separate source, requirements and security reports qualify what the interface actually supports.

Browser: Codex in-app browser, own local-preview server at `127.0.0.1:8843`, synthetic data in a new private temporary root listed in `session.json`. Existing user projects and the user's development server were not used. Viewports: initial narrow browser approximately 600×800; desktop diagnostic override 1440×1000; resumed browser 1280×720. These are browser observations, not evidence of an iPhone/mobile product or native-window qualification. Native default is 1440×900 (`gui/native_window.py:55–57`). Theme Dark and font scale 100% in accepted captures.

The audit was interrupted between criteria/reference creation and assessment. The temporary server stopped; restarting the same private root retained the saved propulsion design but not modern in-memory geometry/study/comparison context. The sphere journey was regenerated through actual UI controls, then assessed and reported. This corroborates documented memory-only limits; it is not a claim that an already-generated report disappeared before the interruption. The downloadable report was generated after resumption.

## Numbered workflow health

1. **Login — working local bootstrap, incomplete lifecycle.** Existing generated credential worked; no password/cookie is recorded. Infrastructure-profile selection and private-preview warning are visible. Some secondary text is visually subdued against a decorative dark backdrop. Password recovery/rotation is not a supported backend journey (repository finding R6); choosing a profile must not be confused with proving that role permissions are enforced.
2. **Projects and navigation — partial, with confirmed defects.** Empty state honestly shows no fabricated projects and directs users to Rocket Engine New. The shell project is explicitly UI-only. Primary V&V is incorrectly disabled as planned; Reports points to project history. Both Projects and Reports appear current on `/app/projects`. Nine catalog workbenches remain planned even with modern flags enabled.
3. **Rocket Engine — functioning preliminary analysis, not complete engine design.** New and explicit synthetic inputs worked. NASA CEA ran and produced a stored performance envelope; performance and scientific limitations were visible. Cycle remains unimplemented and design review incomplete. Saved drafts are distinguished from results. Picker/tree summaries temporarily remained at old name/r0 while active context/design were r9; navigation/reload refreshed them. Target thrust is labeled merely “Thrust,” while actual calculated thrust differs. Default result presentation is text-heavy.
4. **Native Geometry — functioning qualified fixture, not general CAD.** Real OCCT sphere build completed with independent software QA. WebGL display and server-backed two-display-vertex measurement worked. Source B-rep, analytic STEP and coarse display triangulation are explicitly distinguished. Fixed radius, read-only reference dimensions, visual clipping and no engineering publication are honest. It cannot model the active rocket design or edit arbitrary parametric features.
5. **Simulation — functioning restricted benchmark.** Accepted sphere attachment, real run, convergence/conservation monitoring, analytical verification, temperature profiles and source hashes worked. Numerical convergence did not become experimental validation. The model is steady 1D radial sphere conduction, not engine CFD/FEA or a 3D field solver. Long tables, raw hashes and header/dock density reduce scanning efficiency.
6. **Comparison and V&V — functioning evidence preview, poorly discoverable.** Direct route worked despite primary navigation being disabled. Current P09 candidate → predeclared criteria → independent synthetic analytic reference → exact assessment succeeded. Maximum discrepancy was approximately 0.001628 K, within the synthetic 0.01 K limit; output uncertainty correctly remained unknown, not zero. Experimental validation, independent engineering review and production handoff remained not-performed/pending/blocked. This is not measured engine validation.
7. **Knowledge — useful existing breadth, broken preview import boundary.** Modern source/claim navigation and preserved legacy intake/chat/search/graph/review are visible. Empty sources are explicit; no fake citations were seeded. Scoped contextual filtering is not mislabeled as semantic retrieval. Actual imported-document/approved-source journeys were not exercised with user documents. Isolated HTTP probes show packaged multipart uploads are blocked before parsing; role-header approval escalation makes existing governance untrustworthy until fixed.
8. **Reports and history — functioning synthetic package, incomplete general governance.** Current comparison receipt generated an immutable research report; JSON/MD/HTML/ZIP links appeared. ZIP downloaded through the UI and `unzip -t` passed for manifest plus all three report formats. Status stayed current/converged with experimental validation absent, independent signoff pending and handoff blocked. No general rocket-engine report generation, signed acceptance or restart-safe modern history is implemented.

## Prioritized UX findings

### UX-01 — P2: primary navigation contradicts actual feature availability

Visible evidence: `02-navigation.png`, `03-projects-desktop.png`, `07-comparison.png`. The disabled V&V button claims it is planned while its enabled page performs a real assessment. Reports & History opens `/app/projects?view=history`, not the functioning report workbench. Source: `gui/static/app-shell/shell.js:205–216`; actual feature-flagged routes `gui/server.py:463–470`, catalog `:561–570`. Global command search also lacks the newer simulation/comparison/report actions (`shell.js:321–329`).

Impact: users can reasonably conclude that implemented work is missing, or end up in the wrong history. Recommendation: derive primary links and commands from the enabled capability catalog and test actual clicks with flags on/off. Preserve compatibility routes. Path-only active-link comparison (`shell.js:208–209`) also marks both Projects and Reports current; query-aware routing is needed.

### UX-02 — P2: engineering context can display contradictory name/revision summaries

Visible evidence: `04-rocket-performance.png`: active shell context says renamed audit design r9, but persisted-design dropdown still shows the original name/r0. Source: `shell.js:266–278` reloads the active DTO but reloads summary cards only for a new design ID. Picker/tree use cached summaries (`:173,201`) while context uses fresh DTO (`:172`). Manual overview refresh (`:307–315`) or route initialization clears the discrepancy.

Impact: users cannot confidently distinguish historical inspection, current editing and stale UI metadata. Recommendation: refresh/invalidate summary metadata on every persisted revision or rename; keep draft updates separate, without implying historical snapshots are restorable.

### UX-03 — P2: target thrust and computed thrust are not clearly distinguished

Observed synthetic fixture: active design metric read “Thrust 10.00 kN” while CEA result was approximately 5.371 kN for the explicit throat area. The top metric is the requested requirement, not solver output: `gui/static/propulsion-suite.js:524` renders `req.target_thrust` with label “Thrust.” This is a presentation ambiguity, not a claim that CEA returned an incorrect result or that the engine met its target.

Recommendation: explicitly label requested/target versus calculated/achieved values, include mismatch context where relevant, and keep operating conditions visible. Do not silently auto-size or alter inputs to hide the difference.

### UX-04 — P2: packaged intake/photo actions are unusable and upload limits disagree

Repository probes R4 demonstrate HTTP 400 `INVALID_CONTENT_TYPE` for photo and document multipart requests in local-preview before route parsing. The legacy intake still advertises “up to 100 MB” (`gui/static/workbench/knowledge.html:67`; `maharshi.js:356–377`), whereas preview transport bounds all bodies at 16 MiB (`infrastructure/release/security.py:100–108`). Visible source: `08b-legacy-knowledge.png`.

Recommendation: align route-aware safe multipart policy and frontend limit/error messages; test real bounded imports and photos in the packaged profile. Retain origin/framing/path/resource protections. Do not loosen all mutation types or raise limits without qualification.

### UX-05 — P2: shell chrome/docks crowd the engineering workspace

Visible evidence: narrow `02-navigation.png`, desktop `03-projects-desktop.png`, resumed `08-knowledge.png`/`09b-report-generated.png`. Wrapping header controls, a default expanded diagnostics panel and independently scrolling regions leave little room for editor/plots. Focus-workspace actions improve available space, but the header remains prominent and focus is not a unified cross-page workspace strategy.

Source: `gui/static/app-shell/styles.css:2–9` permits a wrapping nonshrinking header up to 40vh; `model.js:22` defaults bottom height to 176px and not collapsed; first narrow launch auto-collapses side panels but not the bottom (`shell.js:63–64`; CSS `:40`). This is a narrow-browser usability observation, not a statement that the native app launches at 600×800.

Recommendation: prioritize a compact, progressive-disclosure context toolbar; make solver-specific diagnostics useful in the relevant workspace; define deliberate narrow and native-minimum layouts. Measure actual editing/viewport usable area instead of merely asserting responsiveness.

### UX-06 — P2: scientific output is raw-text-heavy in Standard mode

Evidence: `04-rocket-performance.png`, `05-geometry.png`, `07-comparison.png`. Important numbers often share a monospaced block with units, long precision, IDs and nested JSON. Some CEA stations/subsystem visuals and newer plots/tables are structured; not every result is raw JSON.

Source: `propulsion-suite.js:278–340,443–474` formats newline text/nested JSON and uses text or `pre`; default Standard mode has no corresponding structured replacement. Narrow parameter columns wrap “Parameter,” “Value,” and “Unit” into fragments when provenance/hash content competes for width (`05b-geometry-overview.png`).

Recommendation: summary metrics + explicit applicability/status + structured value/unit/source tables first; exact canonical JSON and full precision in an inspector/disclosure. Use appropriate significant display precision while retaining exact bytes and units. Protect value/unit columns and horizontally scroll long identifiers instead of breaking table headers.

### UX-07 — P1 completeness gap: context/history is not one engineering project

The shell may name a rocket design while NGG, simulation and reports operate on `p07-software-fixtures`; Knowledge is GLOBAL. Warnings make this explicit, which is good, but no actual project-connected geometry/CAE/report journey exists. Modern history is bounded memory-only; engine history is change-event metadata, not complete restorable input snapshots. See requirements RQ-01/RQ-02 and scientific SCI-01/SCI-04/SCI-06.

Recommendation: select one authorized real engineering use case, then add immutable authoritative project/revision/artifact boundaries and cross-workbench selection. This requires an additive architecture/persistence decision and migration qualification, not a navigation-label fix.

### UX-08 — P2 release qualification gap: whole-flow accessibility and scalability remain unproven

Positive visual/DOM observations: visible focus rings; named buttons/fields/regions; textual maturity/freshness/verification/validation labels rather than color alone; explicit plot axes/units/scale and sampling; keyboard instructions on geometry canvas; undo/redo/refusal states; bounded new tables/trees. The P03 library supplies semantic tokens and reusable scientific controls. Scoped previous axe/keyboard tests are retained evidence, not a fresh full WCAG or VoiceOver certification.

This run did not recruit users, run a full keyboard-only or screen-reader/native engineering journey, qualify 200% font/zoom across every screen, formally measure all contrast ratios, or benchmark large engine meshes/corpora/aggregate browser-worker memory. Login secondary labels are visibly subdued, and nested scrolling/table wrapping deserve targeted checks. Do not infer compliance from green source tests or these screenshots.

Recommendation: declared target-size keyboard/VoiceOver/reflow/contrast tasks, representative large workloads, real user comprehension of CURRENT versus acceptance, and before/after measurements. Use synthetic small-fixture results only within their measured scope.

## Strengths worth preserving

- Real API-owned physics/native operations; the browser does not recreate scientific equations.
- Distinct implementation, freshness, execution, convergence, software verification and physical acceptance labels.
- Honest no-data states and no seeded fake engineering sources/results.
- Explicit SI/display units, exact revision/hash provenance and source-inspection links.
- Independent fixture QA and analytic comparison, no fallback into misleading success.
- Genuine downloaded reproducible report archive, with pending acceptance retained.
- Feature flags/legacy compatibility and reusable semantic scientific component library.

## Screenshot evidence

Every accepted image below was saved and visually inspected during this audit. `06b-simulation-profiles.png` captured an unsettled blank paint and is **not accepted evidence**; it is retained transparently rather than used to claim a UI defect. The settled monitor/profile recaptures are used below. `06-simulation-field.png` captures the anchor position before the profile was fully in view; it is not the final profile proof.

### Login

![Current private-preview login](/Users/vaibhavkumarn/Desktop/COSMOS/COSMOS_0.1/docs/implementation/reviews/2026-10-11_COMPLETE_REVIEW/01-login.png)

### Navigation and project workspace

![Narrow navigation exposes incorrectly planned V&V](/Users/vaibhavkumarn/Desktop/COSMOS/COSMOS_0.1/docs/implementation/reviews/2026-10-11_COMPLETE_REVIEW/02-navigation.png)

![Desktop Projects workspace and contradictory primary links](/Users/vaibhavkumarn/Desktop/COSMOS/COSMOS_0.1/docs/implementation/reviews/2026-10-11_COMPLETE_REVIEW/03-projects-desktop.png)

### Rocket performance

![Actual CEA result, explicit assumptions and stale picker summary](/Users/vaibhavkumarn/Desktop/COSMOS/COSMOS_0.1/docs/implementation/reviews/2026-10-11_COMPLETE_REVIEW/04-rocket-performance.png)

### Native geometry

![Accepted sphere display, fixed inspector and explicit software-only scope](/Users/vaibhavkumarn/Desktop/COSMOS/COSMOS_0.1/docs/implementation/reviews/2026-10-11_COMPLETE_REVIEW/05b-geometry-overview.png)

### Simulation

![Radial computed and independent analytic temperature profiles](/Users/vaibhavkumarn/Desktop/COSMOS/COSMOS_0.1/docs/implementation/reviews/2026-10-11_COMPLETE_REVIEW/06d-simulation-profiles.png)

![Residual, conservation and explicit unvalidated status](/Users/vaibhavkumarn/Desktop/COSMOS/COSMOS_0.1/docs/implementation/reviews/2026-10-11_COMPLETE_REVIEW/06c-simulation-monitor.png)

### Comparison

![Actual assessment, predeclared criteria and blocked handoff](/Users/vaibhavkumarn/Desktop/COSMOS/COSMOS_0.1/docs/implementation/reviews/2026-10-11_COMPLETE_REVIEW/07-comparison.png)

### Knowledge

![Modern provenance navigation, honest absent sources and crowded chrome](/Users/vaibhavkumarn/Desktop/COSMOS/COSMOS_0.1/docs/implementation/reviews/2026-10-11_COMPLETE_REVIEW/08-knowledge.png)

![Preserved legacy intake and advertised upload limit](/Users/vaibhavkumarn/Desktop/COSMOS/COSMOS_0.1/docs/implementation/reviews/2026-10-11_COMPLETE_REVIEW/08b-legacy-knowledge.png)

### Reports

![Generated synthetic research report with pending review and blocked handoff](/Users/vaibhavkumarn/Desktop/COSMOS/COSMOS_0.1/docs/implementation/reviews/2026-10-11_COMPLETE_REVIEW/09b-report-generated.png)

## Evidence scope and next action

After resumption, the captured console-error buffer contained zero errors (`browser-errors-after-resume.json`). This does not establish zero errors in the earlier closed tab, all application routes, real uploads or unvisited workloads. Fresh automated baseline and native checks are in `verification-summary.json`; no standalone Playwright suite or new axe/VoiceOver run is claimed by this review. ZIP integrity passed for `synthetic-ui-report.zip` with four files: manifest, JSON, Markdown and HTML.

First next action: **fix and negatively test backend authorization before further multi-user/production claims**, then address navigation/context and safe packaged uploads. General engine integration and durable history are separate approved feature/architecture work. No fix was implemented during this review.
