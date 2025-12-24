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
echo "你好" | r9s chat --model "$R9S_MODEL"

# 2) Interactive multi-turn
r9s chat --model "$R9S_MODEL" --system-prompt "你是一个严谨的助手"

# 3) Persist history across runs
r9s chat --model "$R9S_MODEL" --history-file .r9s_history.json

# 4) Load extensions (module path or .py file)
r9s chat --model "$R9S_MODEL" --ext example/chat_extension.py

# 5) Switch UI language (default: en)
r9s chat --lang zh-CN --model "$R9S_MODEL"
```
