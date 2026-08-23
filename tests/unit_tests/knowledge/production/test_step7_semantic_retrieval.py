"""Semantic retrieval evaluation tests (Step 7 final completion)."""

from __future__ import annotations

from knowledge.production.semantic_retrieval_evaluation import (
    RetrievalEvaluationCase,
    SemanticRetrievalEvaluator,
)
from tests.fixtures.knowledge.representative_corpus import (
    REPRESENTATIVE_ENGINEERING_CORPUS,
    SEMANTIC_EVALUATION_CASES,
)


def _build_evaluator() -> SemanticRetrievalEvaluator:
    cases = tuple(
        RetrievalEvaluationCase(
            query_id=str(item["query_id"]),
            query_text=str(item["query_text"]),
            relevant_document_ids=tuple(
                str(doc_id) for doc_id in item["relevant_document_ids"]
            ),
            notes=str(item.get("notes", "")),
        )
        for item in SEMANTIC_EVALUATION_CASES
    )
    return SemanticRetrievalEvaluator(
        documents=REPRESENTATIVE_ENGINEERING_CORPUS,
        cases=cases,
        k=5,
    )


def test_neural_semantic_retrieval_beats_deterministic_on_representative_corpus() -> None:
    evaluator = _build_evaluator()
    comparison = evaluator.compare_backends()

    deterministic = comparison["deterministic"]
    neural = comparison["neural"]

    assert neural.recall_at_k >= deterministic.recall_at_k
    assert neural.mrr >= deterministic.mrr
    assert neural.hit_rate >= deterministic.hit_rate


def test_semantic_evaluation_reports_latency() -> None:
    evaluator = _build_evaluator()
    report = evaluator.evaluate_backend(
        __import__(
            "knowledge.embeddings",
            fromlist=["create_embedding_backend"],
        ).create_embedding_backend("neural"),
    )

    assert report.mean_query_latency_ms > 0.0
    assert report.case_count == len(SEMANTIC_EVALUATION_CASES)
