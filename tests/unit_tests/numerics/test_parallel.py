import multiprocessing as mp
from multiprocessing.shared_memory import SharedMemory

import numpy as np
import pytest

from core.exceptions import InvalidInputError
from numerics.parallel.shared_memory import shared_vector
from numerics.parallel.task_scheduler import map_ordered
from numerics.parallel.workload import seeded_jobs
from numerics.random.random_generators import generator


def square(value):
    return value * value


def fail_on_two(value):
    if value == 2:
        raise ValueError("worker-two-failed")
    return value


def seeded_value(job):
    return job.payload + float(generator(job.seed).random())


@pytest.mark.parametrize("backend", ["thread", "process"])
def test_order_replay_shutdown(backend):
    before = {p.pid for p in mp.active_children()}
    assert map_ordered(square, [3, 1, 4, 2], backend=backend, worker_count=2) == (
        9,
        1,
        16,
        4,
    )
    jobs = seeded_jobs([1, 2, 3], seed=42)
    serial = tuple(seeded_value(job) for job in jobs)
    assert map_ordered(seeded_value, jobs, backend=backend, worker_count=2) == serial
    assert {p.pid for p in mp.active_children()} == before


@pytest.mark.parametrize("backend", ["thread", "process"])
def test_exception_propagation_and_shutdown(backend):
    before = {p.pid for p in mp.active_children()}
    with pytest.raises(ValueError, match="worker-two-failed"):
        map_ordered(fail_on_two, [1, 2, 3], backend=backend, worker_count=2)
    assert {p.pid for p in mp.active_children()} == before


def test_bounds_and_no_fallback():
    with pytest.raises(InvalidInputError):
        map_ordered(square, [1], backend="thread", worker_count=33)
    with pytest.raises(InvalidInputError):
        map_ordered(square, [1, 2], backend="thread", worker_count=1, max_jobs=1)
    with pytest.raises(InvalidInputError):
        map_ordered(square, [1], backend="automatic", worker_count=1)


def test_shared_memory_actual_lifecycle():
    with shared_vector([1.0, 2.0, 3.0]) as shared:
        name = shared.name
        other = SharedMemory(name=name)
        try:
            view = np.ndarray((3,), dtype=np.float64, buffer=other.buf)
            np.testing.assert_array_equal(view, [1, 2, 3])
            view[1] = 9
            assert shared.values[1] == 9
            del view
        finally:
            other.close()
    with pytest.raises(FileNotFoundError):
        SharedMemory(name=name)
    with pytest.raises(RuntimeError), shared_vector([1]) as shared:
        failed_name = shared.name
        raise RuntimeError("cleanup-test")
    with pytest.raises(FileNotFoundError):
        SharedMemory(name=failed_name)
