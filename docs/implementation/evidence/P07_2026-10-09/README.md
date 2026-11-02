# P07 handoff evidence

Status: **PARTIAL**, full G5 not passed; P08 not started.

- Start with `P07_IMPLEMENTATION_REPORT.md` for implementation status, exact paths,
  actual fixtures, four unresolved CAD QA failures and the required next work.
- `G5_GATE.json` and `test-summary.json` record the machine-readable decision.
- `runs/final3/fixtures/` contains30 latest native candidate records, actual sources,
  exports, and independent QA observations. Failed outputs are forensic candidates,
  not accepted artifacts. Earlier development runs/logs remain retained.
- `candidate-reaudit.json` verifies byte lineage, repeats independent export QA and
  confirms five three-resolution convergence series without changing failed decisions.
- `native-runtime-manifest.json`, `native-install.json`, `requirements-native-tests.txt`,
  `dependency-inventory.json`, `licenses/` and `LICENSING_AND_NATIVE_DECISION.md`
  document local test-only tools and unclosed distribution/licensing evidence.
- `physics_parity.json`, `source_integrity.json` and `predecessor_integrity.json`
  show unchanged scientific results/source and retained earlier phase evidence.
- `REPRODUCE.md` gives explicit test/build commands and evidence limitations.
- `artifact_hashes.json` seals this evidence and the additive implementation/test
  files. Run `finalize_evidence.py --verify` for read-only integrity verification.

An integrity PASS means evidence is intact. It does **not** mean all geometry tests
pass, G5 is accepted, physical validation exists, native distribution is approved,
or application exports are enabled. No production source, GUI, dependencies, Git
history or remote repository state was changed by P07.
