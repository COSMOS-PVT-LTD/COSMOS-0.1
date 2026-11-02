# Reproduce P07 local software evidence

Run from repository root. The actual scratch paths in `native-runtime-manifest.json`
are ephemeral, explicit trusted test configuration, not deployment configuration.
No native tool is auto-installed or enabled by importing the application.

## Standard regression (no native activation)

```sh
env PYTHONPATH=/tmp/cosmos-p06.dqUQn8/schema-tools .venv-remediation/bin/python -m pytest -q
node --test tests/js/*.test.cjs
.venv-remediation/bin/python -m ruff check core knowledge physics numerics systems api gui infrastructure plugins tests tools
.venv-remediation/bin/python -m mypy core physics numerics systems api infrastructure/geometry plugins/geometry
.venv-remediation/bin/python docs/implementation/evidence/P07_2026-10-09/verify_physics.py
```

The schema-test installation is P06's hash-pinned, optional test-only JSON Schema
closure. Without an explicit native config, the native suite is skipped intentionally.
That skip does not qualify geometry. Existing CEA cache tests change only a generated
timestamp in `cache/cea/test_key.json`; retain that output and restore the captured
pre-P07 247-byte file afterwards. Its expected SHA-256 is in `source_before.json`.

## Explicit native tools

Read `LICENSING_AND_NATIVE_DECISION.md` first. Use a new scratch directory. Install
the exact40 developer wheels with `pip --target`, `--require-hashes`,
`--only-binary=:all:` and `requirements-native-tests.txt`. This lock targets the
tested macOS arm64 / Python3.11 wheel set, not other platforms. Pip's target install
does not place Gmsh's dylib; obtain the exact report-pinned Gmsh wheel, verify its
SHA-256 and extract only its `.data/data/lib/libgmsh.4.15.dylib` into that tool root.

Use P02's source-built, minimal PicoGK ABI26.2 and source-built oneTBB runtime. Do not
run upstream dependency-install scripts, reuse unverified bundled dylibs or mutate
the P02 candidate. Check out PicoGK source commit
`7b30d22f7b550175962e478f626384cd7ab15411` in a separate scratch clone, apply
`plugins/geometry/workers/patches/picogk-vdb-disposal.patch`, and build `net9.0` using
the pinned P02 .NET9.0.318 SDK. Existing system .NET was not changed.

The executed build pattern is below. Replace only trusted scratch paths, and use
fresh intermediate directories for each project. The assembly root contains the
patched managed PicoGK.dll, P02's unchanged SkiaSharp.dll, source-built
picogk.26.2.dylib and source-built libtbb.12.16.dylib. No other upstream binaries
were copied into the qualified worker directory.

```sh
/tmp/cosmos-p02.rOuMVo/dotnet9/dotnet build /tmp/cosmos-p07.yVDtYl/pico-managed/PicoGK.csproj -c Release -f net9.0 -p:BaseIntermediateOutputPath=/tmp/cosmos-p07.yVDtYl/patched-obj/ -p:MSBuildProjectExtensionsPath=/tmp/cosmos-p07.yVDtYl/patched-obj/ -o /tmp/cosmos-p07.yVDtYl/patched-managed
/tmp/cosmos-p02.rOuMVo/dotnet9/dotnet build plugins/geometry/workers/PicoWorker.csproj -c Release -p:PicoGKAssemblyRoot=/tmp/cosmos-p07.yVDtYl/pico-assemblies -p:BaseIntermediateOutputPath=/tmp/cosmos-p07.yVDtYl/pico-obj/ -p:MSBuildProjectExtensionsPath=/tmp/cosmos-p07.yVDtYl/pico-obj/ -o /tmp/cosmos-p07.yVDtYl/pico-worker
/tmp/cosmos-p02.rOuMVo/dotnet9/dotnet build plugins/geometry/workers/probes/WireProbe.csproj -c Release -p:BaseIntermediateOutputPath=/tmp/cosmos-p07.yVDtYl/probe-obj/ -p:MSBuildProjectExtensionsPath=/tmp/cosmos-p07.yVDtYl/probe-obj/ -o /tmp/cosmos-p07.yVDtYl/wire-probe
```

The recorded build environment additionally sets isolated DOTNET_CLI_HOME and
NUGET_PACKAGES and disables telemetry, as captured by logs and the P02 dependency
manifest. Compile success is distinct from fixture correctness.

Generate a fresh run-id using `prepare_native_evidence.py --scratch <absolute>
--dotnet <absolute> --candidate <absolute-dll> --wire-probe <absolute-dll>
--run-id <new-id>`. It creates a local config and runtime/wheel receipts. This is an
explicit operator-controlled utility, not an API endpoint. Protect the config and
runtime directory from untrusted writers. A requalification generates new evidence;
do not overwrite a sealed run. Check all runtime hashes before native execution.

```sh
env P07_NATIVE_CONFIG=/tmp/cosmos-p07.yVDtYl/native-config.json .venv-remediation/bin/python -m pytest -q tests/integration_tests/geometry
env P07_NATIVE_CONFIG=/tmp/cosmos-p07.yVDtYl/native-config.json PYTHONPATH=. .venv-remediation/bin/python docs/implementation/evidence/P07_2026-10-09/reaudit_candidates.py
.venv-remediation/bin/python docs/implementation/evidence/P07_2026-10-09/check_scope.py
.venv-remediation/bin/python docs/implementation/evidence/P07_2026-10-09/finalize_evidence.py --verify
```

The native suite is intentionally **not green** at this handoff: four positive CAD
qualification assertions fail. Those failures remain real test failures, not xfails,
skips or relabeled passes. Independent re-audit can pass while retaining those same
failed decisions. Do not mistake an evidence-integrity PASS for a G5 PASS.

No frontend build/browser exercise, application packaging, remote CI, commit, push,
PR or P08 change was performed in P07. Existing app routes/dependencies remain unchanged.
