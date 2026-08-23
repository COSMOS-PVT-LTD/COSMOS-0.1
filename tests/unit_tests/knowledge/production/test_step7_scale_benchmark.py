"""Gate-6 scale benchmark tests."""

from __future__ import annotations

import json
from pathlib import Path

from knowledge.production.scale_benchmark import (
    ScaleBenchmarkRunner,
    ScaleVerificationResult,
    generate_scale_corpus,
)


def test_generate_scale_corpus_count() -> None:
    corpus = generate_scale_corpus(5)
    assert len(corpus) == 5
    assert corpus[0][0] == "DOC-SCALE-0000"


def test_scale_benchmark_runner_five_documents(tmp_path) -> None:
    runner = ScaleBenchmarkRunner(base_dir=tmp_path / "scale")
    result = runner.run_corpus(5)

    assert result.verification in {
        ScaleVerificationResult.VERIFIED,
        ScaleVerificationResult.PARTIALLY_VERIFIED,
    }
    assert result.registered_document_count == 5
    assert result.ingestion_total_ms > 0
    assert result.query_cold_ms > 0
    assert result.storage_bytes > 0


def test_scale_sweep_produces_report(tmp_path) -> None:
    runner = ScaleBenchmarkRunner(base_dir=tmp_path / "sweep")
    report = runner.run_scale_sweep(scale_points=(5, 10))

    assert len(report.corpus_results) == 2
    payload = json.loads(report.to_json())
    assert payload["scale_points"] == [5, 10]


def test_scale_benchmark_artifacts_writable(tmp_path) -> None:
    runner = ScaleBenchmarkRunner(base_dir=tmp_path / "artifacts")
    report = runner.run_scale_sweep(scale_points=(5,))
    output = tmp_path / "scale_report.json"
    output.write_text(report.to_json(), encoding="utf-8")
    assert output.is_file()
