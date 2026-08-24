# Equation Extraction Qualification Notes

**Date:** 2026-08-24  
**Freeze ID:** `KG-KF-REAL-PDF-OCR-EQ-2026-08-24`  
**PRODUCTION-READY:** NO

## Golden source-grounded corpus (text)

Detected only when the source line actually contains the identity:

| Class | Source-faithful form |
|---|---|
| Algebraic | `a = b + c` |
| Structural | `sigma = p * r / t` |
| Heat conduction | `q = k * dT / dx` |
| Fluid identity | `Re = rho * V * D / mu` |

PDF-native qualification uses the COSMOS Reynolds original and still recovers the exact Tj identity `Re = rho * V * D / mu`.

Provisioned OCR (`KG-KF-PROVISIONED-OCR-2026-08-24`) recovers the source-faithful scanned span `Re =rho* V* D/ mu` and does not rewrite it to the textbook form. That span remains a candidate until governed approval.

## Validation states used

`NOT_VALIDATED`, `VALID`, `INVALID`, `UNKNOWN`, `REVIEW_REQUIRED`, `VALIDATION_FAILURE`, `NON_AUTHORITATIVE`, `AMBIGUOUS`, `EXTRACTION_UNAVAILABLE`

UNKNOWN ≠ PASS. Candidates are never constructed as APPROVED.

## Fail-safe cases demonstrated

- missing equation symbol → no candidate
- ambiguous `u` → AMBIGUOUS / REVIEW_REQUIRED
- invalid dimensions → VALIDATION_FAILURE
- missing provenance → NON_AUTHORITATIVE
- contradictory sources → CONTRADICTION_DETECTED
- native vs OCR text mismatch → REPRESENTATION_CONFLICT
- equation split across pages → only the recovered fragment is kept; the rest is not stitched from memory
- figure/table-only page → no guessed equation

## Canonical equation

A candidate becomes a canonical `knowledge.models.equation.Equation` only after governed approval. Physics gateway consumption continues to use the existing approved-only seed / query surface.
