# Math-OCR Qualification Report

**Document ID:** `COSMOS-KF-MATH-OCR-001`  
**Date:** 2026-08-24  
**Freeze ID:** `KG-KF-FOUNDATION-COMPLETION-2026-08-24`  
**Qualification state:** QUALIFIED FOR DEVELOPMENT  
**PRODUCTION-READY:** NO

## Backend

Replaceable `MathOCRAdapter` (`knowledge/mathocr/`).

Provisioned path: `TesseractMathOCRAdapter` (`cosmos-mathocr-tesseract-span`).  
This is equation-span OCR plus AST reconstruction from recovered/source text. It is **not** pix2tex, nougat, or another dedicated math-OCR engine. Those packages are not installed and are not claimed.

Fail-closed default: `UnavailableMathOCRAdapter`.

## What is produced

When an equation span is available:

- source representation (unmodified)
- normalized representation from the AST
- LaTeX/MathML generated from the AST and labeled as reconstructed-from-source-text
- confidence, backend, backend version, region, image hash

LaTeX is **not** claimed as native math-OCR output.

## Unsupported (explicit)

- stacked visual fractions from pixels
- matrices, integrals, summations as recognized layout
- true Unicode Greek recovery from `eng` Tesseract
- auto-approval of math-OCR results

## Tests

Unavailable adapter invents nothing. Provisioned adapter reconstructs `Re = (rho * V * D) / mu` from source text. Native and scanned pipelines attach math-OCR results without promoting them to APPROVED.
