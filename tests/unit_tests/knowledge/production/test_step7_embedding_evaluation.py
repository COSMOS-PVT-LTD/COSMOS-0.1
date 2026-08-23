"""Gate-6 embedding evaluation tests."""

from __future__ import annotations

from knowledge.production.embedding_evaluation import (
    EmbeddingRecommendation,
    EmbeddingStrategyEvaluator,
)


def test_deterministic_embedding_metrics() -> None:
    metrics = EmbeddingStrategyEvaluator().evaluate_deterministic(dimension=8)

    assert metrics.requires_network is False
    assert metrics.bitwise_deterministic is True
    assert metrics.embed_latency_p50_ms >= 0


def test_embedding_report_defers_neural_without_dependency() -> None:
    report = EmbeddingStrategyEvaluator().build_report(dimension=8)

    assert report.neural_metrics is None
    assert report.recommendation is EmbeddingRecommendation.DEFER_NEURAL_BACKEND
    assert report.retrieval_comparison_available is False
