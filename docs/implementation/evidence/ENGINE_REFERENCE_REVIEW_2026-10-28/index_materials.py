"""Metadata/first-page triage only; does not approve, import or alter references."""

import hashlib
import json
import logging
import signal
import subprocess
from collections import Counter, defaultdict
from pathlib import Path

from pypdf import PdfReader

ROOT = Path("/Users/vaibhavkumarn/Desktop/COSMOS/materials ")
OUT = Path(__file__).parent / "MATERIALS_INVENTORY.json"
logging.getLogger("pypdf").setLevel(logging.CRITICAL)


def timeout(_signal, _frame):
    raise TimeoutError("Metadata/first-page triage exceeded 12-second file budget")


def main():
    signal.signal(signal.SIGALRM, timeout)
    files = sorted(Path(p) for p in subprocess.check_output(["rg", "--files", str(ROOT)], text=True).splitlines())
    records = []
    sized = defaultdict(list)
    for path in files:
        rel = path.relative_to(ROOT)
        stat = path.stat()
        record = {"path":str(path), "relative_path":str(rel), "bytes":stat.st_size,
                  "mtime_ns":stat.st_mtime_ns, "category":rel.parts[0] if len(rel.parts)>1 else "[root]",
                  "extension":path.suffix.lower(), "review_status":"INVENTORIED_ONLY"}
        if path.suffix.lower() == ".pdf":
            signal.alarm(12)
            try:
                reader = PdfReader(path, strict=False)
                record["pages"] = len(reader.pages)
                record["metadata_title"] = str((reader.metadata or {}).get("/Title", ""))[:300]
                first = reader.pages[0].extract_text() or ""
                record["first_page_heading_excerpt"] = " ".join(first.split())[:250]
                record["review_status"] = "METADATA_AND_FIRST_PAGE_TRIAGE_ONLY"
                record["first_page_text_characters"] = len(first)
            except Exception as exc:
                record["parse_error"] = type(exc).__name__ + ": " + str(exc)[:180]
            finally:
                signal.alarm(0)
            sized[stat.st_size].append(path)
        records.append(record)
    duplicates = []
    for paths in sized.values():
        if len(paths)<2:
            continue
        hashes = defaultdict(list)
        for path in paths:
            with path.open("rb") as source:
                digest = hashlib.file_digest(source, "sha256").hexdigest()
            hashes[digest].append(str(path))
        duplicates.extend({"sha256":digest,"paths":paths} for digest,paths in hashes.items() if len(paths)>1)
    result = {"schema":"cosmos.reference-library-triage.v1", "date":"2026-10-28",
              "root":str(ROOT), "scope":"Complete rg-visible inventory; PDF metadata/first-page triage, NOT full reading or scientific acceptance",
              "file_count":len(records), "pdf_count":sum(r["extension"]==".pdf" for r in records),
              "category_counts":dict(Counter(r["category"] for r in records)),
              "parse_error_count":sum("parse_error" in r for r in records),
              "pdf_pages_from_successful_metadata":sum(r.get("pages",0) for r in records),
              "exact_duplicate_pdf_groups":duplicates, "records":records,
              "source_files_changed":False,"baseline_changed":False,"r08_resumed":False}
    with OUT.open("x") as stream:
        json.dump(result, stream, indent=2, ensure_ascii=False)
        stream.write("\n")
    print(json.dumps({k:result[k] for k in ("file_count","pdf_count","category_counts","parse_error_count","pdf_pages_from_successful_metadata")}))
    print("Exact duplicate PDF groups:",len(duplicates),"(none removed)")


if __name__ == "__main__":
    main()
