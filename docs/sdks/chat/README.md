# Chat
(*chat*)

## Overview

### Available Operations

* [create](#create) - Create chat completion

## create

Create a chat completion, supports streaming

### Example Usage

<!-- UsageSnippet language="python" operationID="createChatCompletion" method="post" path="/chat/completions" -->
```python
from r9s import R9S


with R9S(
    api_key="<YOUR_BEARER_TOKEN_HERE>",
) as r9_s:

    res = r9_s.chat.create(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "user",
                "content": "Hello, how are you?",
            },
        ],
        stream=False,
    )

    print(res.choices[0].message.content)

```

For streaming responses, call `chat.create(..., stream=True)` and iterate the returned event stream. When `stream=False`, the SDK returns a normal [models.ChatCompletionResponse](../../models/chatcompletionresponse.md).

### Parameters

| Parameter                                                                                           | Type                                                                                                | Required                                                                                            | Description                                                                                         |
| --------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------- |
| `model`                                                                                             | *str*                                                                                               | :heavy_check_mark:                                                                                  | Model name                                                                                          |
| `messages`                                                                                          | List[[models.Message](../../models/message.md)]                                                     | :heavy_check_mark:                                                                                  | Messages list                                                                                       |
| `frequency_penalty`                                                                                 | *Optional[float]*                                                                                   | :heavy_minus_sign:                                                                                  | Penalizes tokens based on how often they already appeared, reducing repetition                      |
| `logit_bias`                                                                                        | Dict[str, *float*]                                                                                  | :heavy_minus_sign:                                                                                  | Adjusts the likelihood of specific tokens by token ID                                              |
| `logprobs`                                                                                          | *Optional[bool]*                                                                                    | :heavy_minus_sign:                                                                                  | When true, stream must be false (OpenAI constraint)                                                 |
| `top_logprobs`                                                                                      | *Optional[int]*                                                                                     | :heavy_minus_sign:                                                                                  | Number of most likely tokens to return at each position when `logprobs=True`                       |
| `max_tokens`                                                                                        | *Optional[int]*                                                                                     | :heavy_minus_sign:                                                                                  | Legacy token cap for the completion. Prefer `max_completion_tokens` when supported by the model    |
| `n`                                                                                                 | *Optional[int]*                                                                                     | :heavy_minus_sign:                                                                                  | Number of chat completion choices to generate                                                       |
| `modalities`                                                                                        | List[[models.Modalities](../../models/modalities.md)]                                               | :heavy_minus_sign:                                                                                  | Output modality types. Use ["text", "audio"] for audio output                                       |
| `audio`                                                                                             | [Optional[models.Audio]](../../models/audio.md)                                                     | :heavy_minus_sign:                                                                                  | Audio output settings used when `modalities` includes `audio`                                      |
| `presence_penalty`                                                                                  | *Optional[float]*                                                                                   | :heavy_minus_sign:                                                                                  | Penalizes tokens that have already appeared, encouraging new topics                                |
| `response_format`                                                                                   | [Optional[models.ResponseFormat]](../../models/responseformat.md)                                   | :heavy_minus_sign:                                                                                  | Constrains the output format, for example JSON mode or JSON schema                                 |
| `seed`                                                                                              | *Optional[int]*                                                                                     | :heavy_minus_sign:                                                                                  | Best-effort deterministic sampling seed                                                             |
| `service_tier`                                                                                      | [Optional[models.ServiceTier]](../../models/servicetier.md)                                         | :heavy_minus_sign:                                                                                  | Processing tier used to serve the request                                                           |
| `stop`                                                                                              | [Optional[models.Stop]](../../models/stop.md)                                                       | :heavy_minus_sign:                                                                                  | Up to four stop sequences where generation should end                                               |
| `stream`                                                                                            | *Optional[bool]*                                                                                    | :heavy_minus_sign:                                                                                  | When true, returns SSE events instead of a single JSON response                                     |
| `stream_options`                                                                                    | [Optional[models.StreamOptions]](../../models/streamoptions.md)                                     | :heavy_minus_sign:                                                                                  | Extra streaming controls such as whether to include usage stats in the final event                 |
| `temperature`                                                                                       | *Optional[float]*                                                                                   | :heavy_minus_sign:                                                                                  | Sampling temperature. Higher values make output more random                                         |
| `top_p`                                                                                             | *Optional[float]*                                                                                   | :heavy_minus_sign:                                                                                  | Nucleus sampling parameter controlling diversity                                                    |
| `top_k`                                                                                             | *Optional[int]*                                                                                     | :heavy_minus_sign:                                                                                  | Top-k sampling parameter (non-OpenAI standard, model-specific)                                      |
| `tools`                                                                                             | List[[models.Tool](../../models/tool.md)]                                                           | :heavy_minus_sign:                                                                                  | Tool definitions the model may call during generation                                               |
| `tool_choice`                                                                                       | [Optional[models.ChatCompletionRequestToolChoice]](../../models/chatcompletionrequesttoolchoice.md) | :heavy_minus_sign:                                                                                  | Controls whether the model may call tools automatically or must call a specific function            |
| `parallel_tool_calls`                                                                               | *Optional[bool]*                                                                                    | :heavy_minus_sign:                                                                                  | Whether to enable parallel function calling during tool use. Only valid when tools are specified.   |
| `user`                                                                                              | *Optional[str]*                                                                                     | :heavy_minus_sign:                                                                                  | Unique identifier representing end-user for abuse monitoring                                        |
| `reasoning_effort`                                                                                  | [Optional[models.ReasoningEffort]](../../models/reasoningeffort.md)                                 | :heavy_minus_sign:                                                                                  | Reasoning effort level for o1 series models (low, medium, high)                                     |
| `max_completion_tokens`                                                                             | *Optional[int]*                                                                                     | :heavy_minus_sign:                                                                                  | Maximum number of tokens to generate in the completion (alternative to max_tokens, more precise)    |
| `store`                                                                                             | *Optional[bool]*                                                                                    | :heavy_minus_sign:                                                                                  | Whether to store the output for use in model distillation or evals                                  |
| `metadata`                                                                                          | Dict[str, *Any*]                                                                                    | :heavy_minus_sign:                                                                                  | Custom metadata to attach to the request for tracking purposes                                      |
| `retries`                                                                                           | [Optional[utils.RetryConfig]](../../models/utils/retryconfig.md)                                    | :heavy_minus_sign:                                                                                  | Configuration to override the default retry behavior of the client.                                 |

### Response

**[models.CreateChatCompletionResponse](../../models/createchatcompletionresponse.md)**

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
