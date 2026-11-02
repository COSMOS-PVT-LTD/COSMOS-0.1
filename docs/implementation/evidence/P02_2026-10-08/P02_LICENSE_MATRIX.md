# P02 license and dependency review

Scope: exact source pins and packages used in this feasibility investigation. This is engineering due diligence, not legal advice or a distribution approval. `dependency_manifest.json` records commits, inspected-file hashes, NuGet archive hashes, native artifacts, link dependencies, platform load commands and signatures. Copies of the inspected licenses/notices are in `licenses/`.

## Pinned source closure

| Component | Exact revision | License evidence at that revision | P02 use / disposition |
|---|---|---|---|
| PicoGK 2.2.0 | `7b30d22f7b550175962e478f626384cd7ab15411` | [LICENSE](https://github.com/leap71/PicoGK/blob/7b30d22f7b550175962e478f626384cd7ab15411/LICENSE), Apache-2.0 | Managed source build; package metadata agrees. Preserve copyright, license, applicable notices and modification statements when distributing. |
| PicoGKRuntime 2.2.0 / ABI 26.2.0 | `0f26321c18ed878a7820ef769c38fd5d49d39242` | [LICENSE](https://github.com/leap71/PicoGKRuntime/blob/0f26321c18ed878a7820ef769c38fd5d49d39242/LICENSE), Apache-2.0 | C++ source build. Do not run its machine-mutating `Install_Dependencies/Mac.sh`. |
| ShapeKernel 2.1.0 | `313d67601064cf2428e038005afe9ff320b3c56b` | [LICENSE](https://github.com/leap71/LEAP71_ShapeKernel/blob/313d67601064cf2428e038005afe9ff320b3c56b/LICENSE), Apache-2.0 | Source inspection and separate compilation only; not integrated or runtime-validated. |
| OpenVDB 13.0.0 source | `7c03e1f084873cd1b3422c7ff7aec6ee681b3b38` | [LICENSE](https://github.com/AcademySoftwareFoundation/openvdb/blob/7c03e1f084873cd1b3422c7ff7aec6ee681b3b38/LICENSE), Apache-2.0; `RE-LICENSE_NOTE.txt` and core license agree | Runtime's exact gitlink, not floating `master`. Statically linked. Do not substitute historical MPL-2.0 assumptions for this inspected revision. |
| GLFW | `b00e6a8a88ad1b60c0a045e696301deb92c9a13e` | `PicoGKRuntime/GLFW/LICENSE.md`, Zlib | Statically linked; viewer code compiled but no viewer opened. Preserve notice and mark modifications. |
| Dear ImGui | `960921f03a2bf628a802b4611af9fc3c3c9430fe` | `PicoGKRuntime/imgui/LICENSE.txt`, MIT | Compiled viewer dependency, not GUI integration. Preserve copyright and permission notice. |
| ImGui embedded stb headers | Same ImGui pin; full headers retained under `licenses/Dear-ImGui/` | `imstb_truetype.h`, `imstb_rectpack.h`, `imstb_textedit.h`: MIT or public-domain alternative | Use the MIT alternative with notices for future distribution; included source notices must not be omitted. |
| ImGui OpenGL loader / Khronos declarations | Same ImGui pin | `backends/imgui_impl_opengl3_loader.h`: public-domain dedication / Unlicense text and separate Khronos MIT notice | Retain both blocks. A top-level MIT label alone is incomplete. |
| oneTBB 2022.2.0 | `06ce6212da6710f4bb2d20a1904b018aa44069bf` | `oneTBB/LICENSE.txt`, Apache-2.0 | Source built in isolated prefix; dynamic `libtbb.12` loaded. Tests disabled; no HWLOC bind target built. |

The four requested repositories have pinned, permissively licensed source evidence. That finding is not evidence that every precompiled payload has a complete source/notice chain.

## Managed packages and tooling

| Component | Pin / evidence | Findings |
|---|---|---|
| .NET SDK / runtime | SDK 9.0.318, runtime 9.0.20; official archive SHA-512 verified against release metadata; `licenses/dotnet-sdk/` | SDK license is MIT, with separate bundled third-party notices. Existing system SDK 8.0.100 was not changed. SDK is a build/run prerequisite, not a COSMOS dependency update. |
| Microsoft.SourceLink.GitHub, Microsoft.SourceLink.Common, Microsoft.Build.Tasks.Git | 8.0.0; package `.nuspec` source pin `ce7339775f8ada5b16c72a874f591c8cd5722c6b` | MIT metadata; build tooling, not geometry implementation. Private SourceLink dependencies remain in upstream build closure. |
| SkiaSharp; SkiaSharp.NativeAssets.macOS; SkiaSharp.NativeAssets.Win32 | 3.119.0; package metadata source pin `64f24b1cddb68d30ec0ac6b661964178fc21d5ec` | Packages declare MIT and include MIT notices. Underlying native Skia and its third-party closure require their own release SBOM/notices. No Skia rendering path was exercised. Win32 payload was restored transitively, not executed. |
| CMake and Ninja | Isolated Python tool environment: CMake 3.31.6, Ninja 1.11.1.4 | Installed packages retain Apache-2.0 packaging/tool notices and CMake BSD-3-Clause notice; copies and hashes recorded. Build tools only, not shipped into COSMOS. Package metadata/RECORD hashes and install log are recorded. Complete build-tools SBOM and original wheel archive hashes remain release work. |
| Python and NumPy | Existing COSMOS remediation environment, Python 3.11.4 / NumPy 2.4.6 | Independent audit harness only. No new scientific package installed into COSMOS. Not a new production dependency. |
| Apple system frameworks, libc++, libSystem, zlib | Absolute system dependencies enumerated by `otool -L` | Used on this Mac, not copied or redistributed. No claim about other operating systems. |

`worker/packages.lock.json` records the resolved runtime package graph and NuGet content hashes. Full package/source metadata, including private build dependencies, is also in `dependency_manifest.json`.

## Prebuilt and embedded assets: unresolved distribution evidence

The pinned managed repository includes nine arm64 dylibs: PicoGK, Boost iostreams/random/regex, ICU data/i18n/uc, lzma and zstd. All bytes are hashed and link dependencies recorded. The repository does not establish exact source revisions or a complete notice chain for each bundled binary. Names alone are not a license verification. Do not redistribute this bundle as an approved COSMOS package until that closure is established.

The embedded `assets/Jost.ttf` name table identifies the Jost Project Authors and explicitly declares SIL Open Font License 1.1. It is **not** Apache-2.0. Its exact file hash and metadata are recorded. The complete OFL notice and font packaging constraints need release review. `assets/ViewerEnvironment.zip` is hashed, but asset-specific provenance has not been independently established. Both assets are embedded by the upstream managed project even though this headless probe does not render them.

The locally compiled minimal runtime avoids the prebuilt Boost/ICU/lzma/zstd chain for these fixtures: delayed OpenVDB loading, Blosc and Imath-half are disabled. That is a qualified feasibility configuration, not proof of full upstream feature parity. Its source closure is directly traceable, but native relocation, notices, signing, notarization and release-level SBOM still need verification.

## Decision

ALLOW: isolated local source compilation and synthetic geometry investigation with recorded pins and notices.

NOT APPROVED: production redistribution, blanket commercial-license clearance, mixed/unpinned native binaries, or replacing a complete SBOM with this matrix. The upstream binary and embedded-asset gaps are explicit release blockers, separate from the mesh-QA failure described in `P02_FEASIBILITY_REPORT.md`.
