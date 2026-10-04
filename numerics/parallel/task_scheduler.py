"""
COSMOS Rocket Propulsion Platform

Module: numerics.parallel.task_scheduler
Author: COSMOS Development Team
Version: 0.1.0
Purpose: Domain-neutral parallel.task_scheduler foundation.
Copyright (c) 2026 COSMOS PVT LTD. All Rights Reserved.

Description:
    Domain-neutral, normalized numerical data; no physical validity claims.
"""

from __future__ import annotations

from collections.abc import Callable, Iterable

from numerics.parallel import multiprocessing, threading
from numerics.parallel.workload import InputType, OutputType
from numerics.utilities.numerical_checks import invalid


def map_ordered(function: Callable[[InputType],OutputType], items: Iterable[InputType], *,
                backend: str, worker_count: int, max_jobs: int = 10000) -> tuple[OutputType,...]:
    """No implicit backend selection or fallback; ordered outputs in both backends."""
    if backend=="thread":
        return threading.map_ordered(function,items,worker_count=worker_count,max_jobs=max_jobs)
    if backend=="process":
        return multiprocessing.map_ordered(function,items,worker_count=worker_count,max_jobs=max_jobs)
    invalid("Parallel backend must be explicitly thread or process.")
