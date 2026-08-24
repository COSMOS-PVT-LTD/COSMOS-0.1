# Reference Ingestion Qualification Report

**Document ID:** `COSMOS-KF-REF-INGEST-001`  
**Date:** 2026-08-24  
**Freeze ID:** `KG-KF-FOUNDATION-COMPLETION-2026-08-24`  
**Qualification state:** QUALIFIED FOR DEVELOPMENT  
**PRODUCTION-READY:** NO

## Rights

`knowledge.references.rights.RightsStatus`:

`RIGHTS_CLEARED`, `LICENSED`, `PUBLIC_DOMAIN`, `INTERNAL`, `RESTRICTED`, `UNKNOWN`

Ingestible: cleared, licensed, public domain, internal.  
`UNKNOWN` and `RESTRICTED` return `ExtractionStatus.RIGHTS_BLOCKED` and produce no equation candidates.

Legacy `ingest_real_pdf` without an explicit status records `INTERNAL` (COSMOS fixture path). That is an explicit default, not a silent conversion of `UNKNOWN`.

## Document classes

NASA SP/TM/CR, NASA technical report, handbook, rocket propulsion textbook, design manual, research paper, COSMOS internal.

Classes are taxonomy, not copyright exceptions.

## NASA/Huzel-class corpus

Qualified fixture: `nasa_class_fixture.pdf`.

- COSMOS original
- rights `INTERNAL`
- class `NASA_TECHNICAL_REPORT`
- bibliographic envelope only
- **no NASA or Huzel source prose**

The pipeline can process that class. It does not ingest the COSMOS reference library PDFs.

## Editions

Existing `DuplicateKind.DIFFERENT_EDITION` is preserved. Different editions are not merged. SQLite `knowledge_versions` retains approval history.
