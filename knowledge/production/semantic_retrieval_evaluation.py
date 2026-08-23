"""Semantic retrieval evaluation for Gate-6 / final completion."""

from __future__ import annotations

import json
import math
from dataclasses import dataclass
from pathlib import Path

from knowledge.embeddings.protocol import EmbeddingBackend
from knowledge.embeddings.service import create_embedding_backend

__all__ = (
    "RetrievalEvaluationCase",
    "RetrievalEvaluationReport",
    "SemanticRetrievalEvaluator",
)


@dataclass(frozen=True, slots=True, kw_only=True)
class RetrievalEvaluationCase:
    """Single query with expected relevant document IDs."""

    query_id: str
    query_text: str
    relevant_document_ids: tuple[str, ...]
    notes: str = ""


@dataclass(frozen=True, slots=True, kw_only=True)
class RetrievalEvaluationReport:
    """Aggregate retrieval metrics for one backend."""

    backend_id: str
    recall_at_k: float
    precision_at_k: float
    mrr: float
    ndcg_at_k: float
    hit_rate: float
    mean_query_latency_ms: float
    k: int
    case_count: int

    def to_mapping(self) -> dict[str, object]:
        return {
            "backend_id": self.backend_id,
            "case_count": self.case_count,
            "hit_rate": round(self.hit_rate, 4),
            "k": self.k,
            "mean_query_latency_ms": round(self.mean_query_latency_ms, 4),
            "mrr": round(self.mrr, 4),
            "ndcg_at_k": round(self.ndcg_at_k, 4),
            "precision_at_k": round(self.precision_at_k, 4),
            "recall_at_k": round(self.recall_at_k, 4),
        }


def _cosine(a: tuple[float, ...], b: tuple[float, ...]) -> float:
    return sum(left * right for left, right in zip(a, b, strict=True))


class SemanticRetrievalEvaluator:
    """Evaluate semantic retrieval quality against a labeled query set."""

    def __init__(
        self,
        *,
        documents: dict[str, str],
        cases: tuple[RetrievalEvaluationCase, ...],
        k: int = 5,
    ) -> None:
        self._documents = documents
        self._cases = cases
        self._k = k

    def evaluate_backend(self, backend: EmbeddingBackend) -> RetrievalEvaluationReport:
        import time

        doc_vectors = {
            doc_id: backend.embed_document(text)
            for doc_id, text in self._documents.items()
        }

        recalls: list[float] = []
        precisions: list[float] = []
        reciprocal_ranks: list[float] = []
        ndcgs: list[float] = []
        hits: list[float] = []
        latencies: list[float] = []

        for case in self._cases:
            start = time.perf_counter()
            query_vector = backend.embed_query(case.query_text)
            latency_ms = (time.perf_counter() - start) * 1000.0
            latencies.append(latency_ms)

            ranked = sorted(
                doc_vectors.items(),
                key=lambda item: _cosine(query_vector, item[1]),
                reverse=True,
            )
            top_ids = [doc_id for doc_id, _ in ranked[: self._k]]
            relevant = set(case.relevant_document_ids)
            retrieved_relevant = [doc_id for doc_id in top_ids if doc_id in relevant]

            recalls.append(
                len(retrieved_relevant) / len(relevant) if relevant else 0.0,
            )
            precisions.append(len(retrieved_relevant) / self._k if self._k else 0.0)
            hits.append(1.0 if retrieved_relevant else 0.0)

            rr = 0.0
            for rank, doc_id in enumerate(top_ids, start=1):
                if doc_id in relevant:
                    rr = 1.0 / rank
                    break

            reciprocal_ranks.append(rr)

            dcg = sum(
                1.0 / math.log2(rank + 1.0)
                for rank, doc_id in enumerate(top_ids, start=1)
                if doc_id in relevant
            )
            ideal_hits = min(len(relevant), self._k)
            idcg = sum(1.0 / math.log2(rank + 1.0) for rank in range(1, ideal_hits + 1))
            ndcgs.append(dcg / idcg if idcg > 0 else 0.0)

        count = len(self._cases)

        return RetrievalEvaluationReport(
            backend_id=backend.identity.fingerprint(),
            recall_at_k=sum(recalls) / count if count else 0.0,
            precision_at_k=sum(precisions) / count if count else 0.0,
            mrr=sum(reciprocal_ranks) / count if count else 0.0,
            ndcg_at_k=sum(ndcgs) / count if count else 0.0,
            hit_rate=sum(hits) / count if count else 0.0,
            mean_query_latency_ms=sum(latencies) / count if count else 0.0,
            k=self._k,
            case_count=count,
        )

    def compare_backends(
        self,
        *,
        modes: tuple[str, ...] = ("deterministic", "neural"),
    ) -> dict[str, RetrievalEvaluationReport]:
        return {
            mode: self.evaluate_backend(create_embedding_backend(mode))
            for mode in modes
        }

    @staticmethod
    def load_cases(path: Path) -> tuple[RetrievalEvaluationCase, ...]:
        payload = json.loads(path.read_text(encoding="utf-8"))
        cases_raw = payload.get("cases", [])

        if not isinstance(cases_raw, list):
            return ()

        cases: list[RetrievalEvaluationCase] = []

        for item in cases_raw:
            if not isinstance(item, dict):
                continue

            cases.append(
                RetrievalEvaluationCase(
                    query_id=str(item["query_id"]),
                    query_text=str(item["query_text"]),
                    relevant_document_ids=tuple(
                        str(doc_id) for doc_id in item.get("relevant_document_ids", [])
                    ),
                    notes=str(item.get("notes", "")),
                ),
            )

        return tuple(cases)
