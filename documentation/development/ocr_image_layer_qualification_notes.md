# OCR / Image Layer Qualification Notes

**Date:** 2026-08-24  
**Baseline freeze:** `KG-KF-REAL-PDF-OCR-EQ-2026-08-24`  
**Current freeze:** `KG-KF-PROVISIONED-OCR-2026-08-24`  
**PRODUCTION-READY:** NO

## Later freeze addendum

`KG-KF-PROVISIONED-OCR-2026-08-24` provisions local Tesseract 5.4.1 through a controlled subprocess (`knowledge.ocr.tesseract.TesseractOCRAdapter`) and pypdfium2 5.13.0 rasterization. `pytesseract` is not the adapter. Unprovisioned environments still fail closed. Full evidence: `documentation/development/real_pdf_ocr_qualification_report.md`.

The sections below remain the fail-closed baseline from the prior freeze.

## What is implemented

- Page classification: NATIVE_TEXT, IMAGE_ONLY, MIXED, LOW_TEXT_DENSITY, OCR_REQUIRED, EXTRACTION_FAILED
- `OCRAdapter` protocol with default `UnavailableOCRAdapter`
- Optional `TesseractOCRAdapter` used only when the `tesseract` binary is present
- Image SHA-256 hashing and non-destructive preprocess records
- Fail-closed rasterization when no PDF renderer is provisioned
- Embedded JPEG XObject extraction as a raster fallback; no invented pixels
- Hash-addressed OCR cache that does not reuse unavailable results as text
- Equation / table / figure region **candidates** from recovered text only

## Golden OCR behavior

Without a provisioned engine:

```text
image-only PDF
  → rasterize EXTRACTION_UNAVAILABLE (empty image)
  → OCR OCR_UNAVAILABLE / NO_IMAGE
  → text = ""
  → no fabricated equation
```

This is the accepted qualification result. It is not an OCR accuracy score.

## Explicit non-claims

- Cloud OCR is not used
- OCR output is never treated as approved knowledge
- Greek-symbol OCR fidelity is not claimed (`eng` tessdata only)
- CI does not require Tesseract or pypdfium2; provisioned tests skip when absent
