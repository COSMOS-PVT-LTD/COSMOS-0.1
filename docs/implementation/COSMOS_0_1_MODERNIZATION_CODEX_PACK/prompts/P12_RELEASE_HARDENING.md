> **Status:** Developer specification. Not proof of repository implementation.
> **Authority:** Frozen COSMOS architecture PDF is a design baseline, not a current source-code audit. Verify against pinned Git commit before changing files.
> **Language:** Controlled technical English inspired by ASD-STE100 principles. Formal ASD-STE100 compliance is **not certified**. Use short sentences, defined terms, active voice, and one requirement per statement.

# CODEX PHASE P12 — Platform release and freeze

## Execute
Run full regressions, E2E journeys, platform packaging, security/license checks, stress and accessibility tests, migration rollback and release signoff.

## Before coding
1. Read `01_MASTER_CODEX_PROMPT.md` and applicable specs.
2. Inspect actual code with targeted searches. Record paths and symbols.
3. Identify tests, existing components and any frozen architecture conflict.
4. Make a short, file-scoped plan. Avoid duplicating existing functionality.

## Implementation rules
- Deliver the smallest independently testable vertical slice.
- Use typed interfaces, structured diagnostics, SI units and immutable scientific snapshots where applicable.
- Preserve backward compatibility. Keep changes behind a feature flag where feasible.
- Add negative tests, failure recovery and evidence links.
- Do not claim verification or validation without executed tests and recorded results.

## Required outputs
Release evidence, test summary, SBOM, rollback drill, frozen contract registry.

## Gate
Read `acceptance/RELEASE_GATES.md`. Do not pass the phase if its evidence is absent or failed. Store detailed evidence in files; keep chat output under 500 words.

## Final response format (strict)
`PHASE: P12_RELEASE_HARDENING`
`STATUS: PASS | BLOCKED | PARTIAL`
`FILES: <paths, max 12>`
`TESTS: <command and count or NOT RUN>`
`RISKS: <max 3>`
`NEXT: Release complete`
