# Real PDF OCR Qualification Report

**Document ID:** `COSMOS-KF-REAL-PDF-OCR-002`  
**Date:** 2026-08-24  
**Freeze ID:** `KG-KF-PROVISIONED-OCR-2026-08-24`  
**Baseline freeze:** `KG-KF-REAL-PDF-OCR-EQ-2026-08-24`  
**Qualification state:** QUALIFIED FOR DEVELOPMENT  
**PRODUCTION-READY:** NO  
**KG-BLOCK-014:** NOT AUTHORIZED

---

## 1. OCR backend

Local Tesseract via controlled subprocess (`knowledge.ocr.tesseract.TesseractOCRAdapter`).

No cloud OCR. Adapter remains replaceable. `UnavailableOCRAdapter` remains the fail-closed default when the binary is absent.

## 2. OCR version

```text
tesseract 5.4.1
leptonica-1.84.1
language: eng
tessdata: /opt/homebrew/share/tessdata
```

## 3. Rasterizer backend / version

```text
pypdfium2 5.13.0
DPI: 200
format: png
color: rgb
rotation: 0
```

Fallback: embedded JPEG extractor for COSMOS-authored image PDFs. `UnavailableRasterizer` remains available for explicit fail-closed tests.

## 4. Configuration

```text
OCR: lang=eng, psm=6, timeout=60s, low_confidence_threshold=60
Raster: dpi=200, png, rgb
Subprocess: no shell, temp files deleted, OMP_THREAD_LIMIT=1
PDF limits: 25 MiB, 50 pages, %PDF- magic required
```

Configuration hashes are recorded on each raster result.

## 5. Qualification corpus

See `tests/fixtures/knowledge/golden/real_pdf/OCR_CORPUS.json`.

Types covered:

- A. scanned engineering reference (`scanned_reynolds.pdf`)
- B. image-heavy notation (`scanned_notation.pdf`)
- C. mixed native/empty (`mixed_reynolds.pdf`)
- D. equation-heavy (native + scanned Reynolds)
- E. table-heavy (`scanned_table.pdf`)
- F. figure/caption page (Figure 1 on Reynolds originals)

## 6. Rights status

All OCR qualification PDFs are **COSMOS-authored originals**. No NASA/Huzel/library PDFs were ingested.

## 7. Source hashes

| Artifact | SHA-256 |
|---|---|
| scanned_reynolds.pdf | `f7817b92db80ea489b06b9920816e2fe3808cf34151fa360c473068f86c61c57` |
| scanned_table.pdf | `7a9e38bfbe75d519a14fc970b458d24d6dadcb948c495db82f5d188f9ed9db6e` |
| scanned_notation.pdf | `39d988d727c88367230898d60e4c88aec89ffc045e07f700b852f1263168792c` |

## 8. Documents / pages tested

Scanned Reynolds: 1 page. Table: 1 page. Notation: 1 page. Native Reynolds and mixed fixtures remain in the prior freeze.

## 9. Native / scanned classification

Scanned Reynolds pages classify as `IMAGE_ONLY` / `OCR_REQUIRED` (no Tj text layer). Native Reynolds remains `NATIVE_TEXT` and is **not** replaced by OCR.

## 10. OCR results

Recovered scanned Reynolds text includes the identity span. OCR spacing is imperfect and is **retained**:

```text
source-faithful OCR equation span:
Re =rho* V* D/ mu
```

Tesseract mean word confidence ≈ 0.93. 60 TSV word regions. OCR errors are not auto-corrected to `rho * V * D / mu`.

## 11. Region results

Tesseract TSV word regions with bounding boxes, confidence, reading order, and region type are preserved on `OCRResult.regions`.

## 12. Equation results

| Check | Result |
|---|---|
| Equation detected | YES (`Eq. 1` span) |
| Raw OCR representation preserved | YES |
| Symbols Re, rho, V, D, mu recovered | YES |
| Operators `=` `*` `/` preserved | YES |
| Label `Eq. 1` preserved in source line | YES |
| Auto-corrected to textbook form | NO |

Character error rate vs `Re = rho * V * D / mu`: **0.19** (spacing). Word error rate: **0.78** (tokenization of glued symbols). These metrics are reported separately from dimensional validation.

## 13. Variable results

Candidate variables from the OCR span: `Re`, `rho`, `V`, `D`, `mu`. Not approved until review.

## 14. Entity results

Assumption, applicability, figure, table, and Bartz bibliographic mention remain candidate-only when recovered.

## 15. Provenance verification

```text
Approved/reviewed equation
  → OCR equation span
  → OCR regions / page image hash
  → rasterized page (pypdfium2 5.13.0)
  → source PDF SHA-256
  → registered source artifact
```

Hashes persist in `KnowledgeFoundationService.snapshot()["ocr_records"]`. Qualification page image hash:

```text
13be8fe0a4fa18449dbbaa8e9b21ff36efc2b7d57297277a9224ba6ab0ba7cfb
```

## 16. Validation results

Dimensional check on the OCR span: **VALID** (whitespace does not change SI exponents). Overall state before approval: **REVIEW_REQUIRED**. Unit state remains UNKNOWN (no unit tokens on the equation line). UNKNOWN is not treated as PASS.

## 17. Review results

Review package includes excerpt, page, OCR text, OCR confidence, OCR backend, page image hash, validation state, variables, and warnings. Reviewers can reject.

## 18. Approval results

Governed `approve_real_equation` after human decision. OCR_RESULT is never mapped directly to APPROVED.

## 19. Search results

After approval, `search("Re")` retrieves the OCR-derived equation with lifecycle APPROVED and provenance reference.

## 20. Evidence-backed answers

`answer("Re")` exposes supporting entities, source references, validation state, and limitations.

## 21. Negative tests

| Condition | Result |
|---|---|
| Unavailable OCR adapter | empty text, OCR_UNAVAILABLE |
| Unavailable rasterizer | empty image, EXTRACTION_UNAVAILABLE |
| Non-PDF / oversize | CORRUPT_SOURCE |
| Blank image-only page | no invented equation |
| Missing provenance | NON_AUTHORITATIVE |
| Modified source | HASH_MISMATCH |
| Native PDF | OCR not substituted for Tj text |
| Greek/notation mismatch | not silently rewritten |

## 22. Performance

Scanned Reynolds local close-out run (2026-08-24):

| Stage | ms |
|---|---|
| ingest wall | 966 |
| source register | 1.2 |
| page parse | 102 |
| rasterize+OCR | 860 |
| candidate extraction | 1.0 |
| validation | 1.0 |

Correctness over optimization. One OCR page processed. 60 OCR regions. Mean word confidence 0.93.

## 23. Limitations

- Tesseract `eng` only; Greek `ρ`/`μ` are not claimed
- No math-OCR backend
- Vendor/library PDFs not ingested
- CI without Tesseract/pypdfium2 skips provisioned tests and keeps fail-closed tests
- OCR spacing remains visible in the candidate
- Page-image bytes are session evidence; JSON snapshot stores hashes/metadata

## 24. Remaining gaps

- Rights-cleared third-party scanned references
- Math OCR / specialized engineering OCR
- Layout-accurate line reconstruction for all vendor PDFs
- Production monitoring and a production database
- KG-BLOCK-014

## 25. Full regression

```text
1433 passed
5 skipped
0 failed
```

Ruff/mypy on new OCR/raster modules: PASS  
Frozen KG-BLOCK-001→013 and `PdfIngestionAdapter`: not modified  
`provider_invoked`: FALSE

## 26. Qualification decision

```text
QUALIFIED FOR DEVELOPMENT

Not:
  QUALIFIED FOR CONTROLLED USE
  PRODUCTION QUALIFIED
  PRODUCTION-READY = YES
  KG-BLOCK-014 AUTHORIZED
```

COSMOS can ingest a legally usable COSMOS-authored scanned engineering PDF, rasterize it, run local Tesseract, emit source-faithful candidates with provenance, and promote them only through governed approval. That does not authorize production use or KG-BLOCK-014.
