# P00 — Baseline execution evidence

Date: 2026-10-08. Source: `293223ebef190eaa647e67dc581eb186b2b5d987` **plus the existing working tree**, fingerprint `117eaaeae0d56255fc6de4d55f65127d14147b05299c631880b297fc47a53a54`.

No production fixes were made. Commands below describe executed checks, not a proposed test plan. No test result implies hardware validation or release acceptance.

## Environment and isolation

Repository: `/Users/vaibhavkumarn/Desktop/COSMOS/COSMOS_0.1`.

Python executable: `/Users/vaibhavkumarn/Desktop/COSMOS/COSMOS_0.1/.venv-remediation/bin/python` (3.11.4).

Isolated test working directory: `/var/folders/fh/plh1tbm12ln_xy_fj6v8xb480000gn/T/cosmos-p00-baseline-9w8haro8/source`.

Evidence directory: `/Users/vaibhavkumarn/Desktop/COSMOS/COSMOS_0.1/docs/implementation/evidence/P00_2026-10-08`.

`collect_baseline.py` copied fingerprinted source without Git/venv/user data into this temporary directory. `inspect_baseline.py` used temporary DesignStores. Browser testing used a separate application-data directory and server on `127.0.0.1:8790`. Installed distributions, platform and executable are recorded in `repository_baseline.json`. Native tools observed: .NET SDK 8.0.100 and GNU Fortran 14.1.0. Their presence is not proof of all future-kernel compatibility.

## Executed checks

The Python/ruff/mypy executable paths below were from the original `.venv-remediation`; the source/tests working directory was the isolated snapshot unless explicitly stated. `$EVIDENCE` below is only shorthand for the absolute evidence directory above.

| Check | Command | Outcome | Artifact |
|---|---|---|---|
| Full Python suite | `python -m pytest -q --junitxml=$EVIDENCE/pytest.xml` | **2,234 passed, 5 skipped**, 38.45 s; 2,239 collected | `pytest.xml`, `pytest.log` |
| JavaScript tests | `node --test tests/js/*.test.cjs` | **23 passed**, 0 failed, 86.3 ms | `javascript-tests.log` |
| Ruff configured targets | `ruff check core knowledge physics numerics systems api gui infrastructure plugins tests tools` | PASS | `ruff.log` |
| Mypy configured targets | `mypy core physics numerics systems api` | PASS, **318 files** | `mypy.log` |
| Frontend syntax | `node --check` for each `gui/static/*.js` file | PASS | Diagnostic execution; not a browser E2E test |
| Installed dependency compatibility | `python -m pip check` | PASS | Diagnostic execution; not a full locked build |
| Whitespace/change integrity | `git diff --check` in original checkout | PASS | Diagnostic execution |
| Source preservation | `python docs/implementation/evidence/P00_2026-10-08/inspect_baseline.py` | No original fingerprinted files changed | `diagnostic_probes.json` |
| Direct-import policy scan | Same diagnostic helper over `import_edges.json` | Zero forbidden Core/Numerics/Physics direct imports | `diagnostic_probes.json` |
| Numerics refinement/performance | `PYTHONPATH=. python -m tools.benchmark_numerics_foundation` | PASS; **14 three-resolution studies**, **5 microbenchmarks** | `numerics_benchmarks.json`, `numerics_benchmarks_module.log` |
| Native CEA / Fortran reference | `python scripts/verify_cea_reference.py --source-dir "/Users/vaibhavkumarn/Desktop/COSMOS/git-hub repo's/CEA/Win Gui/CEA+Fortran"` | PASS; **3 propellant cases** | `cea_reference.json`, `cea_reference.log` |
| Existing macOS app plist | `plutil -lint "dist/COSMOS 0.1.app/Contents/Info.plist"` | PASS | Diagnostic execution |
| Existing macOS app signature | `codesign --verify --deep --strict "dist/COSMOS 0.1.app"` | **FAIL: code object is not signed at all** | `macos-signature.log` |
| Audit-helper lint | `ruff check docs/implementation/evidence/P00_2026-10-08/collect_baseline.py docs/implementation/evidence/P00_2026-10-08/inspect_baseline.py` | PASS | Final evidence integrity check |

The direct command `python tools/benchmark_numerics_foundation.py` initially failed with `ModuleNotFoundError: numerics` because the script-directory import path did not include the repository root. The successful module invocation above is the documented recovery. Both outcomes are retained; `numerics_benchmarks.log` is the failed invocation, not a passing test log. No production source was patched to hide the failure.

## Python distribution and explicit skips

| Category | Collected | Passed | Skipped |
|---|---:|---:|---:|
| Unit | 1,995 | 1,990 | 5 |
| Integration | 108 | 108 | 0 |
| Regression | 109 | 109 | 0 |
| Benchmark | 8 | 8 | 0 |
| Validation-named fixtures | 19 | 19 | 0 |
| Total | 2,239 | 2,234 | 5 |

| Skipped test (under `tests/unit_tests/knowledge/`) | Recorded reason |
|---|---|
| `test_constant.py::test_constant_hashable` | Nested immutable model dependency |
| `test_dimension.py::test_dimension_hashable` | Reference/Document hashability not implemented |
| `test_engineering_domain.py::test_engineering_domain_hashable` | Document hashability awaits foundation completion |
| `test_subsystem.py::test_subsystem_hashable` | Foundation models not yet fully immutable |
| `test_unit.py::test_unit_hashable` | Document mappingproxy is not yet hashable |

These are known limitations. They are not five successful tests. The `validation_tests` name does not establish experimental rocket-engine validation. JS tests run VM/DOM harnesses, not a full real-browser accessibility or visual-regression suite. Mypy coverage is the configured 318-file scope, not every Knowledge/GUI module.

## Native CEA verification scope

The reference tool compiled and executed the supplied legacy Fortran reference and compared six metrics in each of three cases: liquid methane, liquid hydrogen and RP-1. Metrics include chamber temperature, molecular weight, characteristic velocity, exit temperature/pressure and frozen conductivity. Relative tolerance is 0.003 (0.3%), reflecting the rounded reference outputs. Database/source paths and comparisons are in `cea_reference.json`.

The browser independently exercised the installed native CEA adapter for LOX/LCH4 with chamber pressure 500,000 Pa, O/F 2.7239, expansion ratio 10, reactant temperatures 90.17/111.67 K and throat area 0.001 m². After explicitly saving ambient pressure 0 Pa, thermochemistry and ideal exit performance were current. Representative values: chamber temperature 3093.338429 K; isentropic exponent 1.13250955; molecular weight 0.018985146 kg/mol; c-star 1832.209565 m/s. The screenshot and structured result DOM retain provenance and nonvalidation notices.

Negative browser probe: fuel temperature 300 K caused an out-of-range thermochemistry result and a failed dependent performance result. It did not silently fall back to a table or preserve a current success view. This checks error propagation, not an expanded reactant physical-validity domain.

## Performance measurements and unmeasured budgets

Numerics median warm timings from seven repeats:

| Fixture | Median seconds |
|---|---:|
| Root sqrt(2) | 0.000025875 |
| 16-variable linear solve | 0.000252375 |
| RK4 exponential, 200 steps | 0.00293696 |
| Finite-difference sine, 1,001 samples | 0.000009917 |
| FV diffusion, 32 cells | 0.000868999 |

Latest seven-sample warm login HTTP probe median: approximately **0.416 ms** (`diagnostic_probes.json`). This measures a small loopback response, not cold startup, first-paint, interaction latency or native-window launch. Timings vary by machine/load; no service-level promise is inferred.

Cold startup, peak RSS, large document ingestion, large meshes, native worker crashes, CAD reimport, GPU field rendering and sustained concurrent requests were not measured. Establish fixture-specific budgets after P02/P04 prototypes. Do not invent a global performance or geometry-tolerance number.

## Checks not performed / release exclusions

- Hosted GitHub CI and a clean checkout of the dirty-tree changes were not run. Local/remote SHA agreement is not CI qualification of uncommitted files.
- No production build or packaging mutation was performed. Existing app signature failure is retained; no notarization, Windows or Linux release claim is possible.
- No PicoGK/OCCT/CadQuery/VTK feasibility, license closure, native library distribution or SBOM acceptance was completed. Those belong to P02/P12.
- No full screen-reader/keyboard journey across every workbench, automated WCAG scan, mobile design or native pywebview window smoke test was completed. Browser viewports were 1280×720 and the native minimum 1100×700.
- No physical engine validation, hardware safety assessment, general CFD/FEA qualification or experimental dataset acceptance was completed.

G0 uses the successful baseline checks plus transparently recorded diagnostic failures and gaps. The unsigned package blocks a release decision, not completion of a read-only as-built audit.
