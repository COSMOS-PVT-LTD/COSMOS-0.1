# COSMOS standalone Mac desktop integration — 2026-10-28

## Outcome and exact scope

The final installed receipt is `STATUS-ready.json`; its source/runtime
inventory is `runtime-audit-ready.json`. Earlier status/audit records are
retained as intermediate snapshots, not the latest installed launcher checksum.

The existing implemented COSMOS workspaces are integrated into a self-contained
private installation at `/Users/vaibhavkumarn/Applications/COSMOS Desktop.app`.
`/Users/vaibhavkumarn/Desktop/COSMOS Desktop.app` is a Finder-launchable symbolic
link to that installation. The app has its own native Cocoa/WebKit window, name,
icon, Workspaces/Engineering/Research Tools menus, native file dialogs and an
application-owned loopback backend. Normal use needs neither Terminal nor a
browser, external Python, a checkout virtualenv or a running development server.

This is **desktop-delivery completion for the implemented software**, not
completion of all planned workbenches, scientific models, engine redesign,
manufacturing readiness, physical validation or a public production release.
The renderer still uses the existing HTML/JavaScript/Three.js application inside
WebKit; this is not a rewrite into native CAD widgets. The frozen scientific
module layering and all historical runtime policies were preserved.

The checkout HEAD is `293223ebef190eaa647e67dc581eb186b2b5d987`; the installation
contains an inventoried snapshot of the current dirty working tree, not merely
that committed revision. No commit, push or remote CI run was performed.

## Existing data, not migration

The chooser registers these existing, separate folders:

| Label | Existing root |
|---|---|
| Engine CAD / compact development baseline | `output/picogk-components-2026-10-24/app-data` |
| Main COSMOS workspace | `cosmos_app_data` |

Their actual roots remain under `/Users/vaibhavkumarn/Desktop/COSMOS/COSMOS_0.1`.
No project, account, baseline, history or material library was deleted, moved,
merged, initialized as a replacement or migrated. Opening another existing folder
is available through the native Workspaces menu; that additional registration is
session-local. Missing folders fail visibly instead of creating empty projects.

Before/after the live engine-root startup check, its `metadata.sqlite3` SHA-256
remained `894e98ae4d5e6f1e06681b112036e418f630a320937248f4648955d0d2230602`.
The main root remains
`9ab89201846dfdc581e3fd4ffd5cf98258952b20c5818d9d22bead3ef713aeac`.
Native UI test writes were confined to separately created temporary roots.

## Implementation

- `gui/desktop_runtime.py`: binds its own loopback socket, selects an available
  port, closes HTTP workers and releases the existing project authority lease.
  It never adopts or terminates an unrelated listener.
- `gui/application.py`: native launch is strict; missing desktop dependencies
  no longer silently launch a browser. Explicit `--browser` and `--headless`
  developer paths remain separate.
- `gui/desktop_config.py`: explicit data-folder registrations and explicit
  desktop-only enabling of the implemented shell, managed projects, CAD,
  simulation, comparison and knowledge/report interfaces. Historical preview
  flags remain default-off outside that selected desktop profile.
- `gui/desktop_app.py`: native chooser, same-window engineering routes, explicit
  save/cancel warning when changing data roots, native folder selection and
  cleanup of owned research windows. The bridge accepts registered identifiers,
  not filesystem paths or arbitrary commands. The chooser resolves its bridge
  request before replacing its document and bounds startup feedback at 30 s.
  AppKit activation/icon calls are scheduled on Cocoa's main run loop, and
  startup explicitly presents the primary window rather than relying on focus.
  Close/App-menu Quit confirms before cancelling owned work, and last-window
  closure schedules native termination after cleanup to avoid a windowless
  process preventing subsequent LaunchServices reopen.
- `gui/desktop_research.py`: native input/output pickers for the existing compact
  research generator, explicit backend/voxel choice, confirmation and supervised
  cancellation. It creates a new output subfolder only on an explicit run.
  The 10 GiB free-space guard remains, and R08/qualification warnings are retained.
- `scripts/desktop_launcher.c`, `scripts/desktop_entry.py`: Finder entrypoint
  and packaged-only source/bootstrap paths, local launch diagnostics and no
  external interpreter lookup.
  The launcher selects bundled public macOS system-root certificates for Python
  TLS; no user identities/private keys are exported and TLS verification remains
  enabled. This removes the original interpreter's missing external CA-file path.
- `scripts/build_standalone_desktop.py`: new-target-only packaging, guarded
  recovery of its own incomplete stages, embedded Python 3.11.4, separate NumPy
  2.4.6/CEA 3.3.4 and NumPy 2.2.6/CAD worker environments, OCCT/Gmsh/VTK,
  the existing .NET 9 runtime/PicoGK worker, and the separate unqualified compact
  worker. Only copied Mach-O load paths are rebased; originals remain unchanged.
- `scripts/qualify_desktop_bundle.py`: newly executed bundle-local native
  campaigns and new OCCT/PicoGK admission receipts. Historical reports are not
  rewritten or represented as a new run.
- `scripts/audit_desktop_bundle.py`: static Mach-O dependency audit and packaged
  source inventory. Runtime manifests and code live inside the installed app;
  existing project documents intentionally remain outside it.
- `scripts/launch_cosmos.command` now prefers the installed desktop app.
  `scripts/launch_compact_engine.py` now uses a native window by default;
  `--headless` is the explicit HTTP-only development option.
- `gui/static/cosmos-tokens.css` no longer imports Google Fonts over the network;
  installed fonts and the existing local system fallbacks are used.

## Verification

267 focused Python tests passed, with zero failures/errors/skips in these runs:

| Executed scope | Passed |
|---|---:|
| Bundled OCCT native component construction, STEP/STL/critical-feature QA | 48 |
| Bundled OCCT component HTTP workflow | 7 |
| Bundled driving constraints | 14 |
| Bundled PicoGK field/runtime unit boundaries | 25 |
| Bundled PicoGK native construction/mesh/VDB QA | 37 |
| Bundled PicoGK HTTP workflow | 3 |
| Bundled display reduction, including the existing 16-part engine STL | 5 |
| Final desktop lifecycle, native exports, research guards, packaging | 41 |
| Existing desktop HTTP shell and compact candidate/baseline integration | 11 |
| Existing project authority, release preview and release hardening compatibility | 66 |
| Bundled primary-environment NASA CEA numerical checks | 7 |
| Bundled compact **small-feature** native checks | 3 |

The display workload reads the already saved engine STL. The compact checks use
a small synthetic ring/channel fixture. Neither generated a new complete engine
or performed an R08 campaign. These are selected local regression checks, not a
claim that the entire repository suite or remote CI was run.

The actual packaged Cocoa/WebKit renderer passed login and all eight current
native menu destinations: Projects, Rocket Engine, Native Geometry, Simulation,
Comparison/V&V, Visualization, Knowledge, and Reports/History/Governance. WebGL2
was available. The final run also checked for observed remote top-level HTTP
resource loads. See `native-smoke-ready.json` (isolated data, not hardware data).

Finder/LaunchServices startup was additionally inspected through native
accessibility and screenshots (`desktop-home.png`, `desktop-research.png`).
The Research Tools menu opened a real separate native window; its input picker
opened a real macOS Open panel, then was cancelled without selecting a file or
starting a build. The live Engine CAD folder reached the native login screen.
The original OCCT/PicoGK profiles still pass their original admission checks.
Ruff checks/format checks and shell syntax checks passed for the new launch work.

Final native lifecycle observation: Command-Q showed the explicit Close COSMOS /
Cancel confirmation; confirming removed the application from the running-app
inventory, ended its entrypoint process and released its loopback listener
(`58670`). Both live metadata checksums remained unchanged. Reopening through the
actual Desktop shortcut produced the native chooser again (`desktop-ready.png`).
See `manual-native-lifecycle.json`. The final app is left open on that chooser.

Detailed new native reports/receipts are inside the app at
`Contents/Resources/app/desktop-qualification/`. Compact/desktop/compatibility
JUnit files are retained under the checkout's `output/desktop-*.xml`.

## Remaining boundaries

- Full engine regeneration and R08 remain explicitly **ON_HOLD**. The compact
  research worker is present but not promoted to an engineering-qualified engine
  runtime. Existing preliminary/unsupported model labels are unchanged.
- Standalone means local installed code and runtimes, not bundled user data or
  downloaded AI model weights. Optional external AI/search/provider features
  retain their existing configured-service, credentials and network requirements.
- This private build is for this Mac's Darwin arm64 environment and exact install
  path. Moving the application or changing its runtime/source payload requires a
  new build and new path-bound runtime receipts. User project folders may be
  opened elsewhere through the chooser without assuming migration approval.
- It is locally ad-hoc signed, **not Developer ID signed or notarized**. Public
  distribution, cross-Mac qualification, installer/update delivery and license
  clearance remain separate. No production or hardware-readiness claim is made.
- This is a packaged snapshot: later checkout development does not silently
  alter the installed application. Rebuild/qualify a new package for later code.
- The UI uses private renderer sessions; credentials are not bundled or changed.
  Existing bootstrap-account/security limitations are not repaired by packaging.

## References used for desktop API behavior

The implementation reuses the existing desktop engine. Its menu, close,
file-dialog and native rendering calls were checked against the installed
pywebview 5.4 code and [official API documentation](https://pywebview.flowrl.com/api/).
[Official packaging guidance](https://pywebview.flowrl.com/guide/freezing) and
[macOS packaging notes](https://pyinstaller.org/en/stable/feature-notes.html)
informed the distinction between a source-linked launcher, a local self-contained
application, ad-hoc signing and a notarized distribution. No PyInstaller migration
or third-party packaging dependency was required for this private installation.
