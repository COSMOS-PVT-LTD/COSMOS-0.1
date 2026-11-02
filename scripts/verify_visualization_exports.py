"""Independent inspection of owned UI-exported JSON, CSV, SVG and sidecar."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import xml.etree.ElementTree as ET
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("source", "csv", "svg", "metadata"):
        parser.add_argument(name, type=Path)
    parser.add_argument("--output", type=Path, help="New evidence file; existing receipts are never overwritten")
    args = parser.parse_args()
    source_path, csv_path, svg_path, metadata_path = args.source, args.csv, args.svg, args.metadata
    if any(not path.is_file() or path.stat().st_size > 16 * 1024**2 for path in (source_path, csv_path, svg_path, metadata_path)):
        raise ValueError("Four bounded owned export files are required")
    plot = json.loads(source_path.read_text())
    metadata = json.loads(metadata_path.read_text())
    source = plot["source"]
    actual_hash = hashlib.sha256(source["source_canonical_json"].encode()).hexdigest()
    assert actual_hash == source["content_sha256"]
    assert json.loads(source["source_canonical_json"]) == source["source_record"]
    assert metadata["source"] == source
    assert metadata["x"] == plot["x"] and metadata["y"] == plot["y"]
    assert metadata["uncertainty"] == plot["uncertainty"] == "not quantified"
    with csv_path.open(newline="") as stream:
        rows = list(csv.DictReader(stream))
    x = f'{plot["x"]["label"]} [{plot["x"]["unit"]}]'
    y = f'{plot["y"]["label"]} [{plot["y"]["unit"]}]'
    expected = [(series["name"], series["role"], point) for series in plot["series"] for point in series["points"]]
    assert len(rows) == len(expected)
    for row, (name, role, point) in zip(rows, expected):
        assert (row["series"], row["role"]) == (name, role)
        assert [float(row[x]), float(row[y])] == point
        assert row["content_sha256"] == source["content_sha256"]
    assert json.loads(rows[0]["source_json_first_row"]) == source
    svg = ET.fromstring(svg_path.read_bytes())
    labels = " ".join(svg.itertext())
    assert plot["x"]["label"] in labels and plot["y"]["unit"] in labels
    assert "not quantified" in labels and "physical validation" in labels
    report = {"pass": True, "plot_id": plot["id"], "source_sha256": actual_hash,
        "source_rows": len(plot["rows"]), "exact_series_points": len(expected),
        "csv_values_all_matched": True, "svg_units_and_visible_qualification": True,
        "provenance_source_record_exact": True, "no_physical_validation_claim": True,
        "files": {path.name: hashlib.sha256(path.read_bytes()).hexdigest() for path in (source_path, csv_path, svg_path, metadata_path)}}
    if args.output:
        with args.output.open("x") as stream:
            json.dump(report, stream, indent=2)
            stream.write("\n")
    print(f'Exports PASS: {len(expected)} exact series points, source hash, SVG units/qualification, complete provenance.')


if __name__ == "__main__":
    main()
