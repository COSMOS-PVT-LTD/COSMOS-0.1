"""Step 7 production benchmark suite tests."""

from __future__ import annotations

from knowledge.production.benchmark_suite import ProductionBenchmarkSuite


def test_benchmark_suite_reports_verified_envelope(tmp_path) -> None:
    suite = ProductionBenchmarkSuite(store_root=tmp_path)
    report = suite.run(
        documents=(
            (
                "DOC-A",
                "SRC-A",
                "ART-A",
                "# Doc A\n\nChamber pressure nominal.\n",
            ),
            (
                "DOC-B",
                "SRC-B",
                "ART-B",
                "# Doc B\n\nThrust vector control.\n",
            ),
        ),
        query_text="chamber pressure",
        warm_iterations=1,
    )

    assert report.envelope.multi_document is True
    assert report.envelope.document_count == 2
    assert report.envelope.verified_scale
    assert report.envelope.unverified_scale
    assert report.storage_footprint_bytes > 0
    assert len(report.summaries) >= 5
