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
