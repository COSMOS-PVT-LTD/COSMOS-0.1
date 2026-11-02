# Isolated native restoration / reproduction

This restores the original supported versions for local software fixtures, not another solver or a production installer. No system/Homebrew package, owner app root, credential, trust flag or historical P/G5 receipt was modified. Evidence retains first failures and their resolutions.

## Pins / provenance

| Component | Exact restored identity |
| --- | --- |
| OCP /gmsh /VTK wheels | 7.8.1.1.post1 /4.15.0 /9.3.1, original hash-pinned subset in `../R05_3_2026-10-17/runtime-restore-requirements.txt`; actual wheel identities in `wheels.sha256` |
| Microsoft .NET SDK | 9.0.318 macOS arm64, official `https://builds.dotnet.microsoft.com/dotnet/Sdk/9.0.318/dotnet-sdk-9.0.318-osx-arm64.tar.gz`; original SHA512 checked before extraction, retained in `sdk.sha512` |
| PicoGK managed source | tag PicoGK-v2.2.0, `7b30d22f7b550175962e478f626384cd7ab15411` |
| PicoGKRuntime source | tag PicoGK-v2.2.0, `0f26321c18ed878a7820ef769c38fd5d49d39242` |
| oneTBB | v2022.2.0, `06ce6212da6710f4bb2d20a1904b018aa44069bf` |
| Runtime submodules | openvdb `7c03e1f084873cd1b3422c7ff7aec6ee681b3b38`, GLFW `b00e6a8a88ad1b60c0a045e696301deb92c9a13e`, imgui `960921f03a2bf628a802b4611af9fc3c3c9430fe` |
| Isolated build tooling | cmake3.31.6, ninja1.11.1.4; pip report under temporary root `build-tools-install.json`; not COSMOS dependencies |

The official source clones are `https://github.com/leap71/PicoGK`, `https://github.com/leap71/PicoGKRuntime`, `https://github.com/uxlfoundation/oneTBB`. Pinned submodules used normal checked-out revisions, not `--remote`. No AGENTS files were present in these source trees. Prebuilt Pico dylibs were **not** relabeled as the old qualified build; the native library was rebuilt from source.

Root: `/private/tmp/cosmos-r05_3-native.IcKKdc`. Wheels installed with `--require-hashes --no-deps --target .../cad-tools`; gmsh's wheel data dylib was extracted from that exact checked wheel because pip target layout did not retain it. Direct `OCP`/gmsh imports report7.8.1.1/4.15.0. No CadQuery/VTK top-level GUI import is required by these workers; unrelated VTK modules are not in the runtime manifest.

The managed OpenVdbFile disposal patch is the existing COSMOS `plugins/geometry/workers/patches/picogk-vdb-disposal.patch`, applied only to the isolated source. `picogk-vdb-disposal-applied.patch` records it: transient metadata field wrappers disposed in finally; no geometry equation change.

## Build / test route

Use `P02_2026-10-08/P02_BUILD_AND_REPRODUCE.md` as the historical build recipe, replacing only its temporary root. Fresh logs here record configuration/compilation:

- Build/install oneTBB into `native-deps` with TBB_TEST=OFF, Release, Ninja.
- Configure PicoGKRuntime with PICOGK_UPDATE_SUBMODULES=OFF; static OpenVDB, delayed loading/Blosc/Imath-half/Python/binaries/unit-tests disabled as in the original minimal recipe. Prefix points only to that native-deps. Both use the installed CommandLineTools SDK C++ include workaround recorded in the configure/build logs.
- Build targets `picogk APITests`, one compilation process. APITests compiled; an executed APITests suite is **not** claimed. Python worker/QA tests below are executed native evidence.
- Build managed PicoGK with SDK9.0.318, GeneratePackageOnBuild=false. Copy source-built Pico native dylib and exact TBB/SkiaSharp dependencies to its assembly root, not the cloned prebuilt binary.
- Build current repository `PicoWorker.csproj` using PicoGKAssemblyRoot plus isolated output/intermediate paths. The wire probe first hit duplicate generated attributes because moving the intermediate directory exposed existing repository obj files. The unmodified probe csproj/Program.cs were copied to isolated `wire-source` and compiled there successfully. No owner obj files were deleted and no probe semantics changed.
- Native library links the source-built native-deps path. That is a local qualified layout, **not relocation/distribution proof**.

`manifest.py` generated the initial 113-hash config without a success receipt. Explicit native tests ran before the existing API runtime guard was enabled. After a small coordinator-only transcript-verification change, the six actual managed-native cases were rerun against the final code and a new manifest. `qualify.py` verifies both XML results and the sole initial-vs-final native-manifest difference, then issues a **new local software receipt**. Do not rerun generators over evidence indiscriminately or reseal old G5.

For a future fresh qualification, use a new evidence label/directory; fixture retention refuses overwriting an existing case. The following reuses only the native tests that write replaceable managed/crash receipts; full original fixtures need a fresh destination:

```sh
P07_NATIVE_CONFIG="$PWD/docs/implementation/evidence/R05_3_2026-10-18/runtime-config.json" \
  .venv-release-p12/bin/python -m pytest -q \
  tests/integration_tests/geometry/test_managed_native_retention.py \
  tests/integration_tests/geometry/test_managed_native_crash.py
```

To view the retained synthetic project without owner-data changes, first verify8863 is free, then run from the repository:

```sh
.venv-release-p12/bin/python tests/ui/r05_3/preview.py \
  --root /private/tmp/cosmos-r05_3-preview.tzUIlF --port 8863 --resume --read-only \
  --runtime "$PWD/docs/implementation/evidence/R05_3_2026-10-18/runtime-config.json"
```

Open `http://127.0.0.1:8863/app/projects`. The clearly synthetic QA login is defined in the preview helper, not an owner credential. This checks runtime hashes before opening that exact task root and does not migrate/reset it. If temporary runtimes no longer exist or sources change, the guard should refuse; restore/requalify rather than editing hashes to force acceptance. Production enablement, schema migration and installer/signing remain separate explicit work.
