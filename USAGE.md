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