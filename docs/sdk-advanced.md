# Advanced Python SDK usage

This page covers common advanced patterns when using the `r9s` Python SDK.

## Custom base URL

If you are using a custom r9s deployment or gateway, set `R9S_BASE_URL` in the
environment (or pass `default_base_url` to `R9S.from_env()` for a fallback):

```python
from r9s.client import R9S

with R9S.from_env() as r9s:
    print(r9s.models.list())
```

## Chat completions (streaming)

```python
from r9s.client import R9S

with R9S.from_env() as r9s:
    stream = r9s.chat.create(
        model="gpt-5-mini",
        messages=[{"role": "user", "content": "Write a haiku about databases."}],
        stream=True,
    )

    for event in stream:
        if not event.choices:
            continue
        delta = event.choices[0].delta
        if delta.content:
            print(delta.content, end="", flush=True)
    print()
```

## Responses API (streaming)

```python
from r9s.client import R9S

with R9S.from_env() as r9s:
    stream = r9s.responses.create(
        model="gpt-5-mini",
        input="Draft a short release note for a CLI tool.",
        stream=True,
    )

    for event in stream:
        if event.type == "response.output_text.delta":
            print(event.delta, end="", flush=True)
    print()
```

## Retries and timeouts

Use `timeout_ms` to set a per-operation timeout:

```python
from r9s.client import R9S

with R9S.from_env(timeout_ms=60_000) as r9s:
    print(r9s.models.list())
```

If you need custom retry behavior, pass `retry_config` when constructing `R9S`.

## Async usage

```python
import asyncio
from r9s.client import R9S

async def main() -> None:
    async with R9S.from_env() as r9s:
        res = await r9s.models.list_async()
        print(res)

asyncio.run(main())
```

## Parallel execution

Use `parallel` and `map_parallel` to fan out multiple async SDK calls with a
concurrency limit. Results are wrapped in `CallResult` objects that capture
the value or exception for each call.

```python
import asyncio
from r9s.client import R9S, parallel, map_parallel

async def main() -> None:
    async with R9S.from_env() as r9s:
        results = await parallel(
            [
                r9s.chat.create_async(model="gpt-4o", messages=[{"role": "user", "content": "Hi"}]),
                r9s.chat.create_async(model="gpt-4o", messages=[{"role": "user", "content": "Hey"}]),
            ],
            concurrency=5,
        )

        for r in results:
            if r.ok:
                print(r.value)
            else:
                print(f"Error: {r.error}")

asyncio.run(main())
```

`map_parallel` is a convenience helper that applies an async function to each
item in an iterable:

```python
chunks = ["Summarize this.", "Summarize that."]

results = await map_parallel(
    chunks,
    lambda c: r9s.chat.create_async(
        model="gpt-4o",
        messages=[{"role": "user", "content": c}],
    ),
    concurrency=3,
)
```

Options:

- `concurrency` — maximum number of calls running at once (default `10`)
- `ordered` — if `True` (default), results match input order; if `False`,
  results are returned in completion order
- `stop_on_error` — if `True`, cancel remaining tasks on first failure

Each `CallResult` exposes `ok`, `value`, `error`, `index`, and `latency_ms`.
