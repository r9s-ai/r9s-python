# Proxy
(*proxy*)

## Overview

### Available Operations

* [request](#request) - Proxy request

## request

Proxy requests to target endpoint through specified channel

### Example Usage

<!-- UsageSnippet language="python" operationID="createProxyRequest" method="post" path="/nextrouter/proxy/{channelid}/{target}" -->
```python
from r9s import R9S


with R9S(
    api_key="<YOUR_BEARER_TOKEN_HERE>",
) as r9_s:

    res = r9_s.proxy.request(channelid="123", target="chat/completions", request_body={
        "model": "gpt-4o-mini",
        "messages": [
            {
                "role": "user",
                "content": "Hello",
            },
        ],
    })

    # Handle response
    print(res)

```

### Parameters

| Parameter                                                           | Type                                                                | Required                                                            | Description                                                         | Example                                                             |
| ------------------------------------------------------------------- | ------------------------------------------------------------------- | ------------------------------------------------------------------- | ------------------------------------------------------------------- | ------------------------------------------------------------------- |
| `channelid`                                                         | *str*                                                               | :heavy_check_mark:                                                  | Channel ID                                                          | 123                                                                 |
| `target`                                                            | *str*                                                               | :heavy_check_mark:                                                  | Target path                                                         | chat/completions                                                    |
| `request_body`                                                      | Dict[str, *Any*]                                                    | :heavy_minus_sign:                                                  | N/A                                                                 |                                                                     |
| `retries`                                                           | [Optional[utils.RetryConfig]](../../models/utils/retryconfig.md)    | :heavy_minus_sign:                                                  | Configuration to override the default retry behavior of the client. |                                                                     |

### Response

**[Dict[str, Any]](../../models/.md)**

### Errors

| Error Type                      | Status Code                     | Content Type                    |
| ------------------------------- | ------------------------------- | ------------------------------- |
| errors.BadRequestError          | 400                             | application/json                |
| errors.AuthenticationError      | 401                             | application/json                |
| errors.PermissionDeniedError    | 403                             | application/json                |
| errors.NotFoundError            | 404                             | application/json                |
| errors.UnprocessableEntityError | 422                             | application/json                |
| errors.RateLimitError           | 429                             | application/json                |
| errors.InternalServerError      | 500                             | application/json                |
| errors.ServiceUnavailableError  | 503                             | application/json                |
| errors.R9SDefaultError          | 4XX, 5XX                        | \*/\*                           |