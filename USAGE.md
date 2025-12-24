<!-- Start SDK Example Usage [usage] -->
```python
# Synchronous Example
from r9s import R9S


with R9S(
    api_key="<YOUR_BEARER_TOKEN_HERE>",
) as r9_s:

    res = r9_s.models.list()

    # Handle response
    print(res)
```

</br>

The same SDK client can also be used to make asynchronous requests by importing asyncio.

```python
# Asynchronous Example
import asyncio
from r9s import R9S

async def main():

    async with R9S(
        api_key="<YOUR_BEARER_TOKEN_HERE>",
    ) as r9_s:

        res = await r9_s.models.list_async()

        # Handle response
        print(res)

asyncio.run(main())
```
<!-- End SDK Example Usage [usage] -->

## CLI: Chat

```bash
# 1) Pipe stdin (single-turn)
echo "hello" | r9s chat --model "$R9S_MODEL"

# 2) Interactive multi-turn
r9s chat --model "$R9S_MODEL" --system-prompt "Your task is translate user input to Simplified Chinese, keep the orginal typography"

# 3) History (default: saved under ~/.r9s/chat/)
r9s chat --model "$R9S_MODEL"

# 4) Resume a saved session (interactive selection)
r9s chat resume --model "$R9S_MODEL"

# 5) Load extensions (module path or .py file)
r9s chat --model "$R9S_MODEL" --ext example/chat_extension.py

# 6) Switch UI language (default: en)
r9s chat --lang zh-CN --model "$R9S_MODEL"

# 7) Use a saved bot profile (local)
r9s bot create mybot --model "$R9S_MODEL" --system-prompt "You are a helpful assistant"
r9s chat --bot mybot
```
