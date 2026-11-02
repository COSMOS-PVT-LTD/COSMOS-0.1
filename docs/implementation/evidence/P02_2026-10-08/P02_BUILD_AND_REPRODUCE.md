# P02 build and reproduction

This evidence directory is a stand-alone feasibility harness. Do not add its projects or dependencies to the COSMOS application build. It is expected to fail its complete acceptance run until the recorded geometry defects are resolved.

## Prerequisites and pins

Use the seven exact commits in `dependency_manifest.json`. The managed and runtime sources use matching `PicoGK-v2.2.0` tags; verify the peeled commits, not just tag names. ShapeKernel uses `ShapeKernel-v2.1.0`. OpenVDB, GLFW and ImGui are the runtime's recorded gitlinks. oneTBB uses `v2022.2.0`.

Use a dedicated directory from `mktemp -d`. Do not reuse a production checkout for external source builds. Do not run the upstream `Install_Dependencies/Mac.sh`, Homebrew updates or submodule `--remote` updates. The study used `/tmp/cosmos-p02.rOuMVo` and changed no global SDK/build dependencies.

1. Clone the official source repositories at the manifest's tags/commits. Run `git submodule update --init --depth 1` for the runtime; verify each gitlink against the manifest. Check repository instructions before building.
2. Create a separate Python tooling venv. Install `cmake==3.31.6 ninja==1.11.1.4` there. The captured tool install log records what was installed; these are not COSMOS Python dependencies.
3. Download .NET SDK **9.0.318** arm64 tar archive from the official URL in the manifest. Verify its **SHA-512 before extraction/execution**. The expected checksum is in the manifest; do not select a newer SDK silently. Extract into the temporary `dotnet9/` directory.
4. Set command-scoped `DOTNET_CLI_TELEMETRY_OPTOUT=1`, `DOTNET_CLI_HOME=<scratch>/dotnet-home`, and `NUGET_PACKAGES=<scratch>/nuget`. Do not redefine `HOME` or `CODEX_HOME`.

The examples below show the actual paths used. For a new temporary directory, replace all `/tmp/cosmos-p02.rOuMVo` instances consistently. Run repository-relative commands from `/Users/vaibhavkumarn/Desktop/COSMOS/COSMOS_0.1`.

## Managed build

```sh
env DOTNET_CLI_TELEMETRY_OPTOUT=1 \
  DOTNET_CLI_HOME=/tmp/cosmos-p02.rOuMVo/dotnet-home \
  NUGET_PACKAGES=/tmp/cosmos-p02.rOuMVo/nuget \
  /tmp/cosmos-p02.rOuMVo/dotnet9/dotnet build \
  docs/implementation/evidence/P02_2026-10-08/worker/P02Worker.csproj \
  -c Release \
  -p:PicoGKSourcePath=/tmp/cosmos-p02.rOuMVo/PicoGK \
  -p:WorkerBuildRoot=/tmp/cosmos-p02.rOuMVo/worker-build
```

For a locked restore, run `dotnet restore --locked-mode` on the same project with the same path properties and environment, followed by `dotnet build --no-restore`. The supplied worker lock records the runtime package graph; upstream private build packages are separately pinned by its project and manifest.

The worker writes protocol JSON to stdout and upstream lifecycle text to stderr. It reads at most 8,193 characters, rejects requests over 8,192, validates exactly nine fields, and rejects unsupported units/frames, schema, operation, dimensions, voxel resolution and cycle count before geometry calls. This is a bounded prototype contract, not the future P06 production contract. One request is consumed to EOF per process.

## Native build

Run these from the temporary root after verifying all source pins:

```sh
env PATH=/tmp/cosmos-p02.rOuMVo/build-tools/bin:/usr/bin:/bin \
  /tmp/cosmos-p02.rOuMVo/build-tools/bin/cmake \
  -S oneTBB -B tbb-build-sdk -G Ninja \
  -DCMAKE_BUILD_TYPE=Release -DTBB_TEST=OFF \
  -DCMAKE_CXX_FLAGS='-isystem /Library/Developer/CommandLineTools/SDKs/MacOSX.sdk/usr/include/c++/v1' \
  -DCMAKE_INSTALL_PREFIX=/tmp/cosmos-p02.rOuMVo/native-deps
/tmp/cosmos-p02.rOuMVo/build-tools/bin/cmake --build tbb-build-sdk --parallel 2
/tmp/cosmos-p02.rOuMVo/build-tools/bin/cmake --install tbb-build-sdk

env PATH=/tmp/cosmos-p02.rOuMVo/build-tools/bin:/usr/bin:/bin \
  /tmp/cosmos-p02.rOuMVo/build-tools/bin/cmake \
  -S PicoGKRuntime -B native-minimal-sdk-build -G Ninja \
  -DCMAKE_BUILD_TYPE=Release -DPICOGK_UPDATE_SUBMODULES=OFF \
  -DOPENVDB_BUILD_BINARIES=OFF -DOPENVDB_BUILD_PYTHON_MODULE=OFF \
  -DOPENVDB_BUILD_UNITTESTS=OFF -DOPENVDB_CORE_SHARED=OFF -DOPENVDB_CORE_STATIC=ON \
  -DOPENVDB_USE_DELAYED_LOADING=OFF -DUSE_BLOSC=OFF -DUSE_IMATH_HALF=OFF \
  -DCMAKE_CXX_FLAGS='-isystem /Library/Developer/CommandLineTools/SDKs/MacOSX.sdk/usr/include/c++/v1' \
  -DCMAKE_PREFIX_PATH=/tmp/cosmos-p02.rOuMVo/native-deps
/tmp/cosmos-p02.rOuMVo/build-tools/bin/cmake --build native-minimal-sdk-build \
  --target picogk APITests --parallel 1
```

The explicit standard-header include is a workaround for the installed command-line-tool search failure, not a modification to upstream C++ source. Other machines must verify their own compiler/SDK rather than assume this workaround is necessary.

Create `source-worker/` in the temporary root. Copy the managed worker DLLs and JSON files from `worker-build/bin/net9.0/`, **without the prebuilt dylibs**. Copy `native-minimal-sdk-build/lib/picogk.26.2.0.dylib` to `source-worker/picogk.26.2.dylib`, the exact import filename. The current native rpath loads oneTBB/allocator from `native-deps/lib`; relocation remains unverified. `logs/native-load-trace.log` confirms the loaded binary paths. Do not confuse a compiled `APITests` target with an executed test suite.

## Separate ShapeKernel compilation

```sh
env DOTNET_CLI_TELEMETRY_OPTOUT=1 \
  DOTNET_CLI_HOME=/tmp/cosmos-p02.rOuMVo/dotnet-home \
  NUGET_PACKAGES=/tmp/cosmos-p02.rOuMVo/nuget \
  /tmp/cosmos-p02.rOuMVo/dotnet9/dotnet build \
  docs/implementation/evidence/P02_2026-10-08/shape-probe/ShapeProbe.csproj \
  -c Release \
  -p:PicoGKSourcePath=/tmp/cosmos-p02.rOuMVo/PicoGK \
  -p:ShapeKernelSourcePath=/tmp/cosmos-p02.rOuMVo/LEAP71_ShapeKernel \
  -p:ShapeBuildRoot=/tmp/cosmos-p02.rOuMVo/shape-build
```

This proves source compilation with compatibility warnings, not ShapeKernel geometry/runtime correctness. Do not port it into Python or copy it into production.

## Benchmarks and independent acceptance

Use fresh nonexisting output directories for every run. Raw artifacts are intentionally never overwritten. The following commands completed their suites but return **exit 1**, correctly reflecting 4/21 failed fixture acceptances for each native configuration:

```sh
.venv-remediation/bin/python docs/implementation/evidence/P02_2026-10-08/run_benchmarks.py \
  --dotnet /tmp/cosmos-p02.rOuMVo/dotnet9/dotnet \
  --worker /tmp/cosmos-p02.rOuMVo/worker-build/bin/net9.0/P02Worker.dll \
  --output /tmp/cosmos-p02.rOuMVo/prebuilt-benchmarks-fresh \
  --label upstream-prebuilt --result prebuilt_benchmarks.json

.venv-remediation/bin/python docs/implementation/evidence/P02_2026-10-08/run_benchmarks.py \
  --dotnet /tmp/cosmos-p02.rOuMVo/dotnet9/dotnet \
  --worker /tmp/cosmos-p02.rOuMVo/source-worker/P02Worker.dll \
  --output /tmp/cosmos-p02.rOuMVo/source-benchmarks-fresh \
  --label locally-compiled-native-minimal --result source_benchmarks.json

.venv-remediation/bin/python docs/implementation/evidence/P02_2026-10-08/test_mesh_audit.py
.venv-remediation/bin/python docs/implementation/evidence/P02_2026-10-08/check_integrity.py
git diff --check
```

Do not overwrite original evidence without preserving the earlier run. Supply a different `--result` filename when collecting a subsequent study. Each fixture child has a 45-second timeout, and its observed RSS is checked against 1 GiB. This is **not** OS-enforced memory containment. Mid-computation cancellation, queueing, progress streaming, atomic publication and crash recovery belong to later worker contracts and are not proved here.

The successful native binaries and all raw generated meshes remain in the temporary directory. Five representative raw meshes are permanently copied into `artifacts/`, including all failed local-source cases. Reports, logs, pins, package lock, notices and fixture definitions remain in the repository. Generated initial MSBuild `obj` directories were moved to the temporary build area; no user files were deleted. A final source-integrity comparison confirms preservation of all pre-existing repository files.
