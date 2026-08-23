"""Execute final completion evidence collection (benchmarks + semantic eval)."""

from __future__ import annotations

import json
from pathlib import Path

from knowledge.production.concurrency_benchmark import ConcurrencyBenchmarkRunner
from knowledge.production.scale_benchmark import ScaleBenchmarkRunner
from knowledge.production.semantic_retrieval_evaluation import (
    RetrievalEvaluationCase,
    SemanticRetrievalEvaluator,
)
from tests.fixtures.knowledge.representative_corpus import (
    REPRESENTATIVE_ENGINEERING_CORPUS,
    SEMANTIC_EVALUATION_CASES,
)

__all__ = ("run_final_completion_evidence",)


def _cases_from_fixture() -> tuple[RetrievalEvaluationCase, ...]:
    cases: list[RetrievalEvaluationCase] = []

    for item in SEMANTIC_EVALUATION_CASES:
        relevant_raw = item.get("relevant_document_ids", ())
        relevant_ids = (
            tuple(str(doc_id) for doc_id in relevant_raw)
            if isinstance(relevant_raw, (list, tuple))
            else ()
        )
        cases.append(
            RetrievalEvaluationCase(
                query_id=str(item["query_id"]),
                query_text=str(item["query_text"]),
                relevant_document_ids=relevant_ids,
                notes=str(item.get("notes", "")),
            ),
        )

    return tuple(cases)


def run_final_completion_evidence(output_dir: Path) -> dict[str, Path]:
    """Run benchmarks and write JSON evidence artifacts."""

    output_dir.mkdir(parents=True, exist_ok=True)
    written: dict[str, Path] = {}

    evaluator = SemanticRetrievalEvaluator(
        documents=REPRESENTATIVE_ENGINEERING_CORPUS,
        cases=_cases_from_fixture(),
        k=5,
    )
    semantic_path = output_dir / "knowledge_step7_final_semantic_evaluation_data.json"
    semantic_payload = {
        mode: report.to_mapping()
        for mode, report in evaluator.compare_backends(
            modes=("deterministic", "neural"),
        ).items()
    }
    semantic_path.write_text(json.dumps(semantic_payload, indent=2, sort_keys=True), encoding="utf-8")
    written["semantic_evaluation"] = semantic_path

    scale_runner = ScaleBenchmarkRunner(base_dir=output_dir / "scale-tmp")
    scale_report = scale_runner.run_scale_sweep(scale_points=(5, 25, 50, 100, 250, 500))
    scale_path = output_dir / "knowledge_step7_final_scale_benchmark_data.json"
    scale_path.write_text(scale_report.to_json(), encoding="utf-8")
    written["scale_benchmark"] = scale_path

    concurrency_runner = ConcurrencyBenchmarkRunner(
        base_dir=output_dir / "concurrency-tmp",
    )
    concurrency_report = concurrency_runner.run_sweep(
        document_count=25,
        concurrency_levels=(1, 2, 4, 8),
    )
    concurrency_path = output_dir / "knowledge_step7_final_concurrency_benchmark_data.json"
    concurrency_path.write_text(concurrency_report.to_json(), encoding="utf-8")
    written["concurrency_benchmark"] = concurrency_path

    return written


if __name__ == "__main__":
    artifacts = run_final_completion_evidence(
        Path("documentation/development"),
    )

    for name, path in artifacts.items():
        print(f"{name}: {path}")
