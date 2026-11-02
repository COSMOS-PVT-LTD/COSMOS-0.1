# P07 native dependency decision

ALLOW only isolated local software-fixture work. Production activation, binary
redistribution and blanket commercial clearance are **not approved**. This is
engineering due diligence, not legal advice. No native binary or dependency package
was added to the application environment, release scripts or GUI. All binaries remain
in explicitly configured scratch tool directories. Generated geometry is synthetic.

## Exact evidence

- `native-runtime-manifest.json`: the actual worker, .NET host, native libraries,
  imported OCP extension and its 75 embedded dylibs, Gmsh library, runtime metadata,
  source pins, platform and patch SHA-256. Test setup rechecks all 90 listed files.
- `native-install.json`: executed pip installation report for 40 exact wheel
  archives; `requirements-native-tests.txt` retains versions and hashes of the
  complete resolved developer tool wheel graph. `dependency-inventory.json` is
  an inventory, **not** a completed distribution SBOM.
- The Gmsh wheel's data-file dylib was not installed by pip `--target`. The exact
  downloaded wheel was compared with its installation-report archive digest and
  that dylib was extracted explicitly. No system package or security policy changed.
- Source/native PicoGK closure and its original license notices remain in
  `../P02_2026-10-08/P02_LICENSE_MATRIX.md` and `dependency_manifest.json`.
  The source-built runtime/TBB/SkiaSharp bytes were reused unchanged; P02 evidence
  and candidate binaries were not patched.
- `logs/native-links.txt` records Mach-O load dependencies of the qualified worker
  dylibs, OCP dylibs/extension and Gmsh. This is local linkage observation, not
  a relocation, signing or cross-platform acceptance test.

## License and source limits

| Component | Evidence and scope | Unclosed release work |
|---|---|---|
| PicoGK managed source | Apache-2.0 at `7b30d22f7b550175962e478f626384cd7ab15411`, license copy retained | Upstream Jost font/OFL and embedded viewer assets retain their separate provenance/notice limits |
| PicoGK runtime | P02 source pin `0f26321c18ed878a7820ef769c38fd5d49d39242`, minimal source-built ABI26.2 | No full upstream feature parity or production distribution approval |
| OCP source | Apache-2.0 at release tag commit `d3fe8a125c5911a5d1cecd17007218f390d6fbae` | The installed `cadquery-ocp==7.8.1.1.post1` wheel does not establish its exact source/build-commit/notice chain; do not infer that from a version string |
| OCCT embedded in OCP | Version7.8.1 observed; LGPL-2.1 and OCCT exception source notices retained | Native/source correspondence, complete notices/SBOM and distribution compliance need review |
| CadQuery2.6.1 / VTK9.3.1 | Developer tooling only; installed closure captured, VTK license copy retained | CadQuery import stalls in macOS VTK loading; no application dependency and no OS security bypass |
| Gmsh4.15.0 | Wheel's GPL-v2-or-later notice retained; external independent developer QA process only | Not bundled into COSMOS; any future distribution/licensing choice requires separate review |

The actual backend is explicitly `occt`, using direct OCP. It is not a hidden
fallback from CadQuery. OCCT remained an allowed B-rep implementation in the P07
specification; no architecture substitution was performed. PicoGK process separation
does not by itself solve license obligations or make untrusted code safe.

Sources: [pinned OCP license](https://github.com/CadQuery/OCP/blob/d3fe8a125c5911a5d1cecd17007218f390d6fbae/LICENSE),
[OCCT7.8.1 LGPL notice](https://github.com/Open-Cascade-SAS/OCCT/blob/V7_8_1/LICENSE_LGPL_21.txt),
[OCCT exception](https://github.com/Open-Cascade-SAS/OCCT/blob/V7_8_1/OCCT_LGPL_EXCEPTION.txt),
[Gmsh copying conditions](https://gmsh.info/doc/texinfo/#Copying-conditions).

## Managed disposal patch

The upstream `OpenVdbFile.SaveToFile` obtains an owning temporary field wrapper
through `xField(n)` while writing metadata. The unmodified build emits exports but
fails P07's zero-allocation exit check. A separate managed source checkout was
patched to dispose that temporary wrapper in `finally`, after the same three
metadata assignments. `plugins/geometry/workers/patches/picogk-vdb-disposal.patch`
contains the exact modification and its notice. No geometry operation, tolerance,
native runtime or old candidate changed. The adapter version is explicitly
`picogk-2.2.0.p07v1`, not an unmodified upstream release.

`logs/pico-first.log` retains the observed failure; `logs/patched-build.log` and the
native fixture transcripts establish successful subsequent isolated builds. Every
normal completed worker response is emitted only after all eight native allocation
counters total zero and total managed-owned native memory returns to its baseline.
Failed/empty/cancelled processes are reaped. This is scoped lifecycle evidence,
not a long-duration leak, allocator peak or production reliability qualification.

No upstream patch submission, package publication or redistribution was performed.
