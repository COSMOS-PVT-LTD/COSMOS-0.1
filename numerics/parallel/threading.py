"""
COSMOS Rocket Propulsion Platform

Module: numerics.parallel.threading
Author: COSMOS Development Team
Version: 0.1.0
Purpose: Domain-neutral parallel.threading foundation.
Copyright (c) 2026 COSMOS PVT LTD. All Rights Reserved.

Description:
    Domain-neutral, normalized numerical data; no physical validity claims.
"""

from __future__ import annotations

from collections.abc import Callable, Iterable
from concurrent.futures import ThreadPoolExecutor

from numerics.parallel.workload import InputType, OutputType, bounded_items, workers


def map_ordered(
    function: Callable[[InputType], OutputType],
    items: Iterable[InputType],
    *,
    worker_count: int,
    max_jobs: int = 10000,
) -> tuple[OutputType, ...]:
    """Explicit bounded thread jobs; original exception propagates after shutdown."""
    n = workers(worker_count)
    data = bounded_items(items, max_jobs)
    pool = ThreadPoolExecutor(max_workers=n, thread_name_prefix="cosmos-numerics")
    try:
        futures = [pool.submit(function, item) for item in data]
        return tuple(future.result() for future in futures)
    finally:
        pool.shutdown(wait=True, cancel_futures=True)
