> **Status:** Developer specification. Not proof of repository implementation.
> **Authority:** Frozen COSMOS architecture PDF is a design baseline, not a current source-code audit. Verify against pinned Git commit before changing files.
> **Language:** Controlled technical English inspired by ASD-STE100 principles. Formal ASD-STE100 compliance is **not certified**. Use short sentences, defined terms, active voice, and one requirement per statement.

# Machine-checkable test matrix

| ID | Test | Expected result |
|---|---|---|
| T-001 | Open existing project with legacy shell | No data migration loss |
| T-002 | Toggle new shell off | Existing navigation remains functional |
| T-003 | Round-trip SI quantity to geometry worker | Value and unit unchanged within declared conversion tolerance |
| T-004 | Invalid unit/frame | Request rejected before build |
| T-005 | Same immutable build request twice | Identical manifest semantics; explain nondeterministic binary metadata if any |
| T-006 | Cancel geometry build | No published partial artifact |
| T-007 | Kill worker mid-build | GUI remains live; job fails with typed error |
| T-008 | Primitive volume/centroid reference | Within fixture-specific tolerance |
| T-009 | Thin-wall/Boolean invalid fixture | QA rejects invalid topology |
| T-010 | STEP export and independent reimport | Units, body count, dimensions verified |
| T-011 | Modify upstream parameter | Affected downstream artifacts marked stale |
| T-012 | Reload old revision | Old artifact and evidence preserved |
| T-013 | Nonconverged solver run | UI does not label numerical success |
| T-014 | External result unit mismatch | Comparison blocked or requires explicit conversion |
| T-015 | Keyboard-only task flow | All critical controls reachable |
| T-016 | Large geometry fixture | Meets measured target budgets, no GUI deadlock |
| T-017 | Missing knowledge source | Evidence marked unavailable; no fabricated citation |
| T-018 | Dependency license inventory | Complete pinned license/notice evidence |

Add fixtures, test commands, expected numeric values and tolerances after repository audit. Do not invent them in advance.
