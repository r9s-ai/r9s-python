from __future__ import annotations

import asyncio
import time
from dataclasses import dataclass
from typing import (
    Awaitable,
    Callable,
    Generic,
    Iterable,
    Optional,
    Sequence,
    TypeVar,
    Union,
)

T = TypeVar("T")
U = TypeVar("U")


@dataclass
class CallResult(Generic[T]):
    """Result wrapper for a single parallel call."""

    ok: bool
    value: Optional[T] = None
    error: Optional[BaseException] = None
    index: int = 0
    latency_ms: int = 0


async def parallel(
    tasks: Sequence[Union[Awaitable[T], Callable[[], Awaitable[T]]]],
    *,
    concurrency: int = 10,
    ordered: bool = True,
    stop_on_error: bool = False,
) -> list[CallResult[T]]:
    """Run awaitables/callables concurrently with a concurrency limit.

    Args:
        tasks: Awaitables or zero-arg async callables to execute.
        concurrency: Maximum number of concurrent tasks.
        ordered: If True, results maintain input order. If False, results are
            returned in completion order.
        stop_on_error: If True, cancel remaining tasks on first failure.

    Returns:
        A list of ``CallResult`` objects.
    """
    if not tasks:
        return []

    sem = asyncio.Semaphore(concurrency)
    results: list[CallResult[T]] = []
    error_event = asyncio.Event() if stop_on_error else None

    async def _run(idx: int, item: Union[Awaitable[T], Callable[[], Awaitable[T]]]) -> CallResult[T]:
        async with sem:
            if error_event and error_event.is_set():
                return CallResult(ok=False, error=asyncio.CancelledError(), index=idx)

            t0 = time.monotonic()
            try:
                coro = item() if callable(item) else item
                value = await coro
                latency = int((time.monotonic() - t0) * 1000)
                return CallResult(ok=True, value=value, index=idx, latency_ms=latency)
            except BaseException as exc:
                latency = int((time.monotonic() - t0) * 1000)
                if error_event:
                    error_event.set()
                return CallResult(ok=False, error=exc, index=idx, latency_ms=latency)

    if ordered:
        async_tasks = [asyncio.ensure_future(_run(i, t)) for i, t in enumerate(tasks)]
        raw = await asyncio.gather(*async_tasks)
        return list(raw)
    else:
        async_tasks = [asyncio.ensure_future(_run(i, t)) for i, t in enumerate(tasks)]
        for coro in asyncio.as_completed(async_tasks):
            results.append(await coro)
        return results


async def map_parallel(
    items: Iterable[U],
    fn: Callable[[U], Awaitable[T]],
    *,
    concurrency: int = 10,
    ordered: bool = True,
    stop_on_error: bool = False,
) -> list[CallResult[T]]:
    """Apply *fn* to each item and run the resulting coroutines concurrently.

    This is a convenience wrapper around :func:`parallel` that produces
    callables from *items* + *fn*, ensuring coroutines are created lazily
    inside the semaphore.

    Args:
        items: Input values to map over.
        fn: An async function applied to each item.
        concurrency: Maximum number of concurrent calls.
        ordered: If True, results maintain input order.
        stop_on_error: If True, cancel remaining tasks on first failure.
    """
    callables: list[Callable[[], Awaitable[T]]] = [
        (lambda bound=item: fn(bound)) for item in items  # type: ignore[misc]
    ]
    return await parallel(
        callables,
        concurrency=concurrency,
        ordered=ordered,
        stop_on_error=stop_on_error,
    )
