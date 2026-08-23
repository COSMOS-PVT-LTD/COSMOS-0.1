"""Deterministic identity helpers for W11 interface packages."""

from __future__ import annotations

import hashlib

__all__ = (
    "deterministic_context_package_id",
    "deterministic_cursor_context_id",
    "deterministic_engineering_payload_id",
    "deterministic_package_digest",
)


def deterministic_package_digest(*stable_parts: str) -> str:
    """Return a deterministic digest for interface packages."""

    canonical = "|".join(stable_parts)

    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def deterministic_context_package_id(request_id: str, package_digest: str) -> str:
    digest = hashlib.sha256(
        f"{request_id}|{package_digest}".encode("utf-8"),
    ).hexdigest()[:16]

    return f"pkg-{digest}"


def deterministic_cursor_context_id(
    project_id: str,
    engineering_task_id: str,
    package_digest: str,
) -> str:
    digest = hashlib.sha256(
        f"{project_id}|{engineering_task_id}|{package_digest}".encode("utf-8"),
    ).hexdigest()[:16]

    return f"ctx-{digest}"


def deterministic_engineering_payload_id(
    cursor_context_id: str,
    outcome_classification: str,
) -> str:
    digest = hashlib.sha256(
        f"{cursor_context_id}|{outcome_classification}".encode("utf-8"),
    ).hexdigest()[:16]

    return f"ekp-{digest}"
