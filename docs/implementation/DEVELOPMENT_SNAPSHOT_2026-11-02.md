# Development snapshot — 2026-11-02

This branch preserves the accumulated COSMOS source, tests, desktop/UI work,
documentation and retained reports since base commit
`293223ebef190eaa647e67dc581eb186b2b5d987`. It is a development backup for review,
not a release or an engineering acceptance decision. R08 remains on hold.

Included work covers the existing project/evidence persistence, desktop lifecycle,
workbenches and visualization, calculation/geometry integrations, recovery tools,
and the separate fixed visual-concept illustration. Historical phase reports keep
their original scope and date; their results do not certify this new snapshot.

## Publication boundaries

- Local databases, user app data, virtual environments, native runtime/build
  caches and generated native geometry remain on the local machine.
- Generated review ZIPs, copies of reference media, local library/machine
  inventories and selected identity-bearing session exports are excluded.
- The small existing STEP reference required by the validation regression is
  retained explicitly. Vendor assets retain their pinned notices and licenses.
- Git attributes preserve original bytes for retained audit evidence, vendor
  assets and source patches; those files are not reformatted by normalization.
- No project history or local artifact was deleted for publication.

## Fresh local pre-publication checks

- JavaScript suite: **505 passed**, zero failures.
- Ruff on the CI production/test paths: **53 findings**, including import sorting
  and other existing source issues. No lint-clean claim is made.
- Mypy on the CI paths: **4 findings across 2 files**, covering missing ReportLab
  stubs and the optional GuidedAPI type in `api/project_authority.py`.
- Full Python suite was started; its final result is reported in the publication
  handoff. Native qualification cases may require separate local runtime profiles.
- Known-token/private-key pattern scan of the staged text found no matches.
- Staged whitespace check passed after preserving raw evidence/vendor bytes.

GitHub Actions runs on `codex/**` pushes. Its result must be read for the exact
pushed commit; the local checks above are not a remote CI result. This snapshot
does not alter repository ownership, rewrite existing history or merge into main.
