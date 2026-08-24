# Real PDF / OCR / Equation Gap Matrix

**Date:** 2026-08-24  
**Baseline freeze:** `KG-KF-REAL-PDF-OCR-EQ-2026-08-24`  
**Current freeze:** `KG-KF-FOUNDATION-COMPLETION-2026-08-24`  
**OCR freeze:** `KG-KF-PROVISIONED-OCR-2026-08-24`

Disposition key: A implemented, B reused existing, C fail-closed / not provisioned, D out of scope.  
Where a cell is dual-valued, the second value is the unprovisioned/CI path.

| ID | Requirement | Disposition | Notes |
|---|---|---|---|
| RF-001 | Source registration | A | `knowledge.pdf.registry.SourceRegistry` |
| RF-002 | Content hashing | B/A | existing `sha256_bytes_digest` + registry |
| RF-003 | Duplicate detection | A | exact / renamed / edition / modified |
| RF-010 | Native-text PDF | A | Tj-operator extractor; optional pypdf |
| RF-011 | Scanned PDF | A / C | OCR when Tesseract+rasterizer provisioned; EXTRACTION_UNAVAILABLE otherwise |
| RF-012 | Mixed PDF | A | per-page; empty pages not fabricated |
| RF-013 | Extraction diagnostics | A | `PdfDiagnostics` |
| RF-020 | Paragraphs | A | from recovered lines |
| RF-021 | Headings | A | Chapter / `1.1` patterns |
| RF-022 | Captions | A | Figure / Table lines |
| RF-030 | Equation candidates | A | `detect_source_equations` |
| RF-031 | Source representation | A | raw text retained; LaTeX only if present |
| RF-032 | Equation provenance | A/B | `ProvenanceTrace` |
| RF-033 | Variables | A/B | new detector + existing candidate extractor |
| RF-034 | Equation validation | A | staged states, UNKNOWN ≠ PASS |
| RF-040 | Variable candidates | B/A | existing extractor on recovered text |
| RF-041 | Constants | A | explicit `symbol = value` only |
| RF-050–052 | Canonicalize / aliases | B/A | existing taxonomy; persist after approve |
| RF-060–063 | Provenance | A/B | page/section/source hash |
| RF-070–075 | Validation stages | A | schema/source/unit/dimension/semantic/applicability |
| RF-080–082 | Governance / review package | A/B | existing approval pipeline + review package |
| RF-090–094 | Persist / graph / search / answer | A/B | service commit + existing search |
| OI-001 | Rasterize | A / C | pypdfium2 when importable; UnavailableRasterizer otherwise |
| OI-002 | Embedded images | A / C | JPEG XObject bytes extracted as raster fallback; no invented pixels |
| OI-003 | Image hash | A | SHA-256 of raster/page image bytes |
| OCR adapter | Engine abstraction | A | protocol + unavailable + local Tesseract subprocess when binary present |
| EQ conflicts | Representation / source | A | no silent winner |
| Frozen PDF adapter | W1 envelope | B | **not modified** |
| Math-OCR | A / C | tesseract-equation-span when Tesseract present; unavailable otherwise |
| Equation AST | A | source-faithful parse; hypothesized Greek is review-only |
| Rights gate | A | UNKNOWN/RESTRICTED → RIGHTS_BLOCKED |
| SQLite persistence | A | additive; JSON snapshot preserved |
| KG-BLOCK-014 | Next block | D | not authorized |
| External library PDFs | NASA/Huzel corpus | D | rights / not in this qualification |
