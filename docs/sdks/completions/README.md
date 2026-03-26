# Completions
(*completions*)

## Overview

### Available Operations

* [create](#create) - Create text completion

## create

Create a legacy text completion endpoint for compatibility use cases

### Example Usage

<!-- UsageSnippet language="python" operationID="createCompletion" method="post" path="/completions" -->
```python
from r9s import R9S


with R9S(
    api_key="<YOUR_BEARER_TOKEN_HERE>",
) as r9_s:

    res = r9_s.completions.create(
        model="gpt-3.5-turbo-instruct",
        prompt="Once upon a time",
        max_tokens=50,
        stream=False,
    )

    print(res.choices[0].text)

```

For streaming responses, call `completions.create(..., stream=True)` and iterate the returned event stream. When `stream=False`, the SDK returns a normal [models.CompletionResponse](../../models/completionresponse.md).

### Parameters

| Parameter                                                                       | Type                                                                            | Required                                                                        | Description                                                                     |
| ------------------------------------------------------------------------------- | ------------------------------------------------------------------------------- | ------------------------------------------------------------------------------- | ------------------------------------------------------------------------------- |
| `model`                                                                         | *str*                                                                           | :heavy_check_mark:                                                              | Model name                                                                      |
| `prompt`                                                                        | *str*                                                                           | :heavy_check_mark:                                                              | Prompt text                                                                     |
| `best_of`                                                                       | *Optional[int]*                                                                 | :heavy_minus_sign:                                                              | Generate multiple results and return the best one                               |
| `echo`                                                                          | *Optional[bool]*                                                                | :heavy_minus_sign:                                                              | Whether to echo the prompt                                                      |
| `frequency_penalty`                                                             | *Optional[float]*                                                               | :heavy_minus_sign:                                                              | Penalizes tokens based on how often they already appeared, reducing repetition |
| `logit_bias`                                                                    | Dict[str, *float*]                                                              | :heavy_minus_sign:                                                              | Adjusts the likelihood of specific tokens by token ID                         |
| `max_tokens`                                                                    | *Optional[int]*                                                                 | :heavy_minus_sign:                                                              | Maximum number of tokens to generate                                          |
| `n`                                                                             | *Optional[int]*                                                                 | :heavy_minus_sign:                                                              | Number of completion choices to generate                                      |
| `presence_penalty`                                                              | *Optional[float]*                                                               | :heavy_minus_sign:                                                              | Penalizes tokens that have already appeared, encouraging new topics          |
| `seed`                                                                          | *Optional[int]*                                                                 | :heavy_minus_sign:                                                              | Best-effort deterministic sampling seed                                       |
| `stop`                                                                          | [Optional[models.CompletionRequestStop]](../../models/completionrequeststop.md) | :heavy_minus_sign:                                                              | Up to four stop sequences where generation should end                         |
| `stream`                                                                        | *Optional[bool]*                                                                | :heavy_minus_sign:                                                              | When true, returns SSE events instead of a single JSON response               |
| `temperature`                                                                   | *Optional[float]*                                                               | :heavy_minus_sign:                                                              | Sampling temperature. Higher values make output more random                   |
| `top_p`                                                                         | *Optional[float]*                                                               | :heavy_minus_sign:                                                              | Nucleus sampling parameter controlling diversity                              |
| `user`                                                                          | *Optional[str]*                                                                 | :heavy_minus_sign:                                                              | End-user identifier for abuse monitoring                                      |
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
