"""Independently compare an owned UI CSV with a freshly read source API DTO."""
from __future__ import annotations

import csv
import hashlib
import json
import sys
from pathlib import Path


def main():
    packet_path, csv_path, destination = map(Path, sys.argv[1:4])
    if any(not path.is_file() or path.stat().st_size > 16 * 1024**2 for path in (packet_path, csv_path)):
        raise ValueError("Two bounded owned evidence files are required")
    packet = json.loads(packet_path.read_text())
    with csv_path.open(newline="") as stream:
        rows = list(csv.DictReader(stream))
    source = json.loads(rows[0]["source_json_first_row"])
    plot = next(item for item in packet["plots"] if item["source"] == source and
        f'{item["y"]["label"]} [{item["y"]["unit"]}]' in rows[0])
    actual_hash = hashlib.sha256(source["source_canonical_json"].encode()).hexdigest()
    assert actual_hash == source["content_sha256"]
    assert json.loads(source["source_canonical_json"]) == source["source_record"]
    x = f'{plot["x"]["label"]} [{plot["x"]["unit"]}]'
    y = f'{plot["y"]["label"]} [{plot["y"]["unit"]}]'
    expected = [(series["name"], series["role"], point) for series in plot["series"] for point in series["points"]]
    assert len(rows) == len(expected)
    for row, (name, role, point) in zip(rows, expected):
        assert (row["series"], row["role"]) == (name, role)
        assert [float(row[x]), float(row[y])] == point
        assert row["content_sha256"] == actual_hash
    report = {"pass": True, "scope": "Actual UI CSV versus independent current API source; not JSON/SVG download qualification",
        "plot_id": plot["id"], "exact_series_points": len(expected), "source_sha256": actual_hash,
        "exact_canonical_text_preserved": True, "csv_values_all_matched": True,
        "validation_not_upgraded": source["validation"],
        "files": {str(path): hashlib.sha256(path.read_bytes()).hexdigest() for path in (packet_path, csv_path)}}
    destination.write_text(json.dumps(report, indent=2) + "\n")
    print(f'UI CSV PASS: {len(expected)} exact points, current API source, canonical source hash.')


if __name__ == "__main__":
    main()
