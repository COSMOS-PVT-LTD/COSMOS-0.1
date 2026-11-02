# P06 evidence and reproduction

Read `P06_IMPLEMENTATION_REPORT.md` and `P06_CONTRACT_DECISION.json` first.
`artifact_hashes.json` seals current P06 source/tests/evidence plus the retained P05
manifest. Logs under `logs/` are ignored by the repository's existing global rule;
they exist locally and are hashed, but must be preserved explicitly if publishing
this evidence later. No ignore rules or prior phase evidence were changed.

## Read-only retained evidence verification

From the repository root:

```sh
.venv-remediation/bin/python docs/implementation/evidence/P06_2026-10-09/finalize_evidence.py --verify
```

This checks hashes, current source scope and executed result records. It does not
rerun tests. A changed HEAD or prior/new source/evidence hash causes rejection. Later
phases should retain this historical seal, not overwrite it to fit their additions.
Do not run P05's historical strict-scope verifier after adding later phases; P06 checks
its 71 retained sealed entries read-only. P05's verifier ran before P06 implementation.

## Rerun tests on this host

The schema test lock includes the exact CPython 3.11 macOS arm64 `rpds-py` wheel.
Other platforms require an independently resolved/audited test-only closure. Run from
the repository root, with the existing environment; no production package install is
needed. A fresh temporary target isolates the optional schema validator:

```sh
p06_test_tools=$(mktemp -d /tmp/cosmos-p06-schema.XXXXXX)
.venv-remediation/bin/python -m pip install --target "$p06_test_tools" --require-hashes --only-binary=:all: -r docs/implementation/evidence/P06_2026-10-09/requirements-schema-tests.txt
PYTHONPATH="$p06_test_tools" .venv-remediation/bin/python -m pytest -q tests/unit_tests/systems_layer/test_geometry_*.py tests/contracts/geometry
PYTHONPATH="$p06_test_tools" .venv-remediation/bin/python -m pytest -q
node --test tests/js/*.test.cjs
.venv-remediation/bin/python -m ruff check core knowledge physics numerics systems api gui infrastructure plugins tests tools
.venv-remediation/bin/python -m mypy core physics numerics systems api
```

Expected: 204 focused passes; 2476 full Python passes and five existing Knowledge
hashability skips; 94 JS passes; Ruff PASS; Mypy 325 sources PASS. If `jsonschema` is
not installed, its optional module will skip; that is **not** the complete P06 evidence
run. The retained focused run has zero skips and executes the independent validator.

The existing full suite updates `cache/cea/test_key.json`'s `created_at`. Preserve its
pre-run bytes, inspect the generated diff and restore only the known generated change
before comparing source scope. Do not reset unrelated dirty work. P06 retained the
generated copy and restored the checkpoint hash
`6ea2f6250df4143d6ca452a552a3dfbae7e5f6a87d2613cd566f0b0dc0fa2508`.

`verify_physics.py` reruns five actual scientific HTTP cases with an ephemeral server
and writes **P06** parity evidence only. `benchmark_contracts.py` writes host-specific
synthetic metadata cost observations, not a geometry-performance acceptance claim:

```sh
.venv-remediation/bin/python docs/implementation/evidence/P06_2026-10-09/verify_physics.py
PYTHONPATH=. .venv-remediation/bin/python docs/implementation/evidence/P06_2026-10-09/benchmark_contracts.py
.venv-remediation/bin/python docs/implementation/evidence/P06_2026-10-09/check_scope.py
```

Those commands intentionally update current P06 evidence and will invalidate a prior
seal; keep historical records separately when re-auditing. `finalize_evidence.py <output>`
is the phase sealing command, not a way to bypass failing evidence. It requires the
recorded test logs/XML, 1808-file checkpoint, predecessor seal and exact scientific
baseline. No native worker, GUI redesign, real geometry or release approval is implied.
