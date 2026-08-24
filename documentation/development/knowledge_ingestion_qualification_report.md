# Knowledge Ingestion Qualification Report (Workspace)

**Document ID:** `COSMOS-KW-INGEST-QUAL-001`  
**Date:** 2026-08-24  
**Freeze ID:** `KG-KF-WORKSPACE-BRAIN-2026-08-24`

```text
PRODUCTION-READY = NO
```

## Gateway

`knowledge.ingest(file, filename=...)` classifies, hashes, rights-checks, vaults, jobs, and routes:

| Format | Route | Notes |
|---|---|---|
| PDF | `ingest_real_pdf` | Frozen PDF adapter untouched |
| Markdown/TXT/LaTeX | `ingest_markdown` | Source-faithful UTF-8 |
| CSV/JSON/XLSX | dataset extractors | Units only from `name (unit)` headers |
| DOCX/PPTX/HTML/EPUB | workspace office/html extractors | Text only; images UNAVAILABLE |
| PNG/JPEG/TIFF/WEBP | `run_ocr` | UNAVAILABLE if Tesseract absent; never invented |
| Unknown | `UNSUPPORTED_FORMAT` | Job FAILED |

## Fail-closed cases tested

- Path traversal filenames
- Empty payload
- Oversize (unit helper)
- UNKNOWN/RESTRICTED rights (`RIGHTS_BLOCKED`, original retained)
- Duplicate fingerprint replay
- Modified same filename → `MODIFIED_SOURCE` + parent
- Reprocess `workspace-2.0.0` keeps original bytes
- Malformed JSON

## Golden fixtures

COSMOS-authored only (`knowledge/workspace/corpus.py`): cooling markdown, chamber CSV, component JSON, XML/HTML notes, minimal office/EPUB bytes, 1×1 PNG. No NASA/Huzel prose.

## Residual

- Dedicated math-OCR still absent.
- Office table/image extraction is partial/unavailable as declared in the capability registry.
- Job execution is local-synchronous, not a durable async worker fleet.
