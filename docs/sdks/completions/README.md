# Completions
(*completions*)

## Overview

### Available Operations

* [create](#create) - Create text completion

## create

Create a text completion, supports streaming

### Example Usage

<!-- UsageSnippet language="python" operationID="createCompletion" method="post" path="/completions" -->
```python
from r9s import R9S


with R9S(
    api_key="<YOUR_BEARER_TOKEN_HERE>",
) as r9_s:

    res = r9_s.completions.create(model="gpt-4o-mini", prompt="Once upon a time", echo=False, frequency_penalty=0, max_tokens=50, n=1, presence_penalty=0, stream=False, temperature=1, top_p=1)

    with res as event_stream:
        for event in event_stream:
            # handle event
            print(event, flush=True)

```

### Parameters

| Parameter                                                                       | Type                                                                            | Required                                                                        | Description                                                                     |
| ------------------------------------------------------------------------------- | ------------------------------------------------------------------------------- | ------------------------------------------------------------------------------- | ------------------------------------------------------------------------------- |
| `model`                                                                         | *str*                                                                           | :heavy_check_mark:                                                              | Model name                                                                      |
| `prompt`                                                                        | *str*                                                                           | :heavy_check_mark:                                                              | Prompt text                                                                     |
| `best_of`                                                                       | *Optional[int]*                                                                 | :heavy_minus_sign:                                                              | Generate multiple results and return the best one                               |
| `echo`                                                                          | *Optional[bool]*                                                                | :heavy_minus_sign:                                                              | Whether to echo the prompt                                                      |
| `frequency_penalty`                                                             | *Optional[float]*                                                               | :heavy_minus_sign:                                                              | N/A                                                                             |
| `logit_bias`                                                                    | Dict[str, *float*]                                                              | :heavy_minus_sign:                                                              | N/A                                                                             |
| `max_tokens`                                                                    | *Optional[int]*                                                                 | :heavy_minus_sign:                                                              | N/A                                                                             |
| `n`                                                                             | *Optional[int]*                                                                 | :heavy_minus_sign:                                                              | N/A                                                                             |
| `presence_penalty`                                                              | *Optional[float]*                                                               | :heavy_minus_sign:                                                              | N/A                                                                             |
| `seed`                                                                          | *Optional[int]*                                                                 | :heavy_minus_sign:                                                              | N/A                                                                             |
| `stop`                                                                          | [Optional[models.CompletionRequestStop]](../../models/completionrequeststop.md) | :heavy_minus_sign:                                                              | N/A                                                                             |
| `stream`                                                                        | *Optional[bool]*                                                                | :heavy_minus_sign:                                                              | N/A                                                                             |
| `temperature`                                                                   | *Optional[float]*                                                               | :heavy_minus_sign:                                                              | N/A                                                                             |
| `top_p`                                                                         | *Optional[float]*                                                               | :heavy_minus_sign:                                                              | N/A                                                                             |
| `user`                                                                          | *Optional[str]*                                                                 | :heavy_minus_sign:                                                              | N/A                                                                             |
| `retries`                                                                       | [Optional[utils.RetryConfig]](../../models/utils/retryconfig.md)                | :heavy_minus_sign:                                                              | Configuration to override the default retry behavior of the client.             |

### Response

**[models.CreateCompletionResponse](../../models/createcompletionresponse.md)**

### Errors

| Error Type                      | Status Code                     | Content Type                    |
| ------------------------------- | ------------------------------- | ------------------------------- |
| errors.BadRequestError          | 400                             | application/json                |
| errors.AuthenticationError      | 401                             | application/json                |
| errors.PermissionDeniedError    | 403                             | application/json                |
| errors.UnprocessableEntityError | 422                             | application/json                |
| errors.RateLimitError           | 429                             | application/json                |
| errors.InternalServerError      | 500                             | application/json                |
| errors.ServiceUnavailableError  | 503                             | application/json                |
| errors.R9SDefaultError          | 4XX, 5XX                        | \*/\*                           |