> **Status:** Developer specification. Not proof of repository implementation.
> **Authority:** Frozen COSMOS architecture PDF is a design baseline, not a current source-code audit. Verify against pinned Git commit before changing files.
> **Language:** Controlled technical English inspired by ASD-STE100 principles. Formal ASD-STE100 compliance is **not certified**. Use short sentences, defined terms, active voice, and one requirement per statement.

# Engineering governance and requirements

## Requirement classes
- **MUST:** release-blocking requirement.
- **SHOULD:** preferred requirement. Document deviations.
- **MAY:** optional capability. Never claim it as implemented without tests.

## GOV requirements
- GOV-001 MUST preserve existing scientific behavior unless a separately approved physics change is required.
- GOV-002 MUST pin dependency versions and record reproducible build commands.
- GOV-003 MUST keep calculation input, configuration, result, and provenance immutable after publication.
- GOV-004 MUST distinguish execution state, numerical termination, physical checks, verification and validation.
- GOV-005 MUST require independent acceptance for geometry exports and simulation handoff.
- GOV-006 MUST document each architecture deviation in an ADR before merge.
- GOV-007 MUST keep workbench UI responsive during long-running jobs.
- GOV-008 MUST provide a tested rollback path for the new application shell and NGG.
- GOV-009 MUST mark unsupported operations and absent source evidence explicitly.
- GOV-010 MUST use typed errors, structured logs, correlation IDs and no silent fallback.

## Engineering review
An engineering reviewer signs a geometry or simulation artifact only after reviewing its evidence. The UI may show 'build complete' without claiming 'design verified' or 'experimentally validated'.

## Documentation language
Use a controlled vocabulary: **parameter**, **snapshot**, **geometry feature**, **artifact**, **study**, **run**, **verification**, **validation**, **stale**. Define each term once. Avoid ambiguous terms such as 'perfect', 'optimized', 'safe', or 'production-ready' without a measurable acceptance basis.
