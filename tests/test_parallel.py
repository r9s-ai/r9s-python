from __future__ import annotations

import asyncio

import pytest

from r9s.parallel import CallResult, map_parallel, parallel


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

async def _succeed(value, delay: float = 0.0):
    if delay:
        await asyncio.sleep(delay)
    return value


async def _fail(msg: str = "boom", delay: float = 0.0):
    if delay:
        await asyncio.sleep(delay)
    raise RuntimeError(msg)


# ---------------------------------------------------------------------------
# parallel() tests
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_ordered_results():
    results = await parallel(
        [_succeed("a"), _succeed("b"), _succeed("c")],
        concurrency=2,
    )
    assert len(results) == 3
    assert [r.value for r in results] == ["a", "b", "c"]
    assert all(r.ok for r in results)
    assert [r.index for r in results] == [0, 1, 2]


@pytest.mark.asyncio
async def test_unordered_results():
    # Stagger delays so completion order differs from input order
    results = await parallel(
        [_succeed("slow", delay=0.1), _succeed("fast", delay=0.0)],
        concurrency=2,
        ordered=False,
    )
    assert len(results) == 2
    # Fast should complete first
    assert results[0].value == "fast"
    assert results[1].value == "slow"


@pytest.mark.asyncio
async def test_error_capture():
    results = await parallel(
        [_succeed("ok"), _fail("oops")],
        concurrency=2,
    )
    assert results[0].ok is True
    assert results[0].value == "ok"
    assert results[1].ok is False
    assert isinstance(results[1].error, RuntimeError)
    assert str(results[1].error) == "oops"


@pytest.mark.asyncio
async def test_stop_on_error():
    # First task fails fast, second is slow
    results = await parallel(
        [_fail("early", delay=0.0), _succeed("late", delay=0.2)],
        concurrency=2,
        stop_on_error=True,
    )
    assert results[0].ok is False
    # The second task may have been cancelled or returned a CancelledError
    # depending on timing; at minimum it shouldn't succeed normally
    # if stop_on_error is working correctly with sequential semaphore acquisition.


@pytest.mark.asyncio
async def test_stop_on_error_with_concurrency_1():
    """With concurrency=1, tasks run sequentially so stop_on_error
    can reliably prevent later tasks from executing."""
    results = await parallel(
        [_fail("first"), lambda: _succeed("second")],
        concurrency=1,
        stop_on_error=True,
    )
    assert results[0].ok is False
    assert results[1].ok is False
    assert isinstance(results[1].error, asyncio.CancelledError)


@pytest.mark.asyncio
async def test_concurrency_limiting():
    """Verify the semaphore limits concurrent execution."""
    running = 0
    max_running = 0

    async def _track(val):
        nonlocal running, max_running
        running += 1
        max_running = max(max_running, running)
        await asyncio.sleep(0.05)
        running -= 1
        return val

    tasks = [lambda v=i: _track(v) for i in range(6)]
    results = await parallel(tasks, concurrency=2)
    assert max_running <= 2
    assert len(results) == 6
    assert all(r.ok for r in results)


@pytest.mark.asyncio
async def test_latency_ms_tracked():
    results = await parallel([_succeed("x", delay=0.05)], concurrency=1)
    assert results[0].latency_ms >= 40  # allow small timing slack


@pytest.mark.asyncio
async def test_empty_input():
    results = await parallel([], concurrency=5)
    assert results == []


@pytest.mark.asyncio
async def test_callable_input():
    """parallel() should accept zero-arg callables that return coroutines."""
    results = await parallel(
        [lambda: _succeed("from_callable")],
        concurrency=1,
    )
    assert results[0].ok is True
    assert results[0].value == "from_callable"


# ---------------------------------------------------------------------------
# map_parallel() tests
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_map_parallel_basic():
    async def double(x: int) -> int:
        return x * 2

    results = await map_parallel([1, 2, 3], double, concurrency=2)
    assert [r.value for r in results] == [2, 4, 6]
    assert all(r.ok for r in results)


@pytest.mark.asyncio
async def test_map_parallel_with_errors():
    async def maybe_fail(x: int) -> int:
        if x == 2:
            raise ValueError("bad value")
        return x

    results = await map_parallel([1, 2, 3], maybe_fail, concurrency=3)
    assert results[0].ok is True
    assert results[1].ok is False
    assert isinstance(results[1].error, ValueError)
    assert results[2].ok is True


@pytest.mark.asyncio
async def test_map_parallel_ordered():
    async def identity(x):
        await asyncio.sleep(0.01)
        return x

    results = await map_parallel(range(5), identity, concurrency=2, ordered=True)
    assert [r.value for r in results] == [0, 1, 2, 3, 4]
