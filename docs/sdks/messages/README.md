# Messages
(*messages*)

## Overview

### Available Operations

* [create](#create) - Create message (Claude native API)

## create

Create a message using Anthropic Claude's native API format, supports streaming

### Example Usage

<!-- UsageSnippet language="python" operationID="createMessage" method="post" path="/messages" -->
```python
from r9s import R9S


with R9S(
    api_key="<YOUR_BEARER_TOKEN_HERE>",
) as r9_s:

    res = r9_s.messages.create(model="claude-opus-4.5", messages=[
        {
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": "Hello, Claude!",
                },
            ],
        },
    ], max_tokens=1024, stream=False, service_tier="auto")

    with res as event_stream:
        for event in event_stream:
            # handle event
            print(event, flush=True)

```

### Parameters

| Parameter                                                                                                                                                                                           | Type                                                                                                                                                                                                | Required                                                                                                                                                                                            | Description                                                                                                                                                                                         |
| --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `model`                                                                                                                                                                                             | *str*                                                                                                                                                                                               | :heavy_check_mark:                                                                                                                                                                                  | Claude model name                                                                                                                                                                                   |
| `messages`                                                                                                                                                                                          | List[[models.AnthropicMessageMessage](../../models/anthropicmessagemessage.md)]                                                                                                                     | :heavy_check_mark:                                                                                                                                                                                  | Messages list, first message must be a user message                                                                                                                                                 |
| `system`                                                                                                                                                                                            | *Optional[str]*                                                                                                                                                                                     | :heavy_minus_sign:                                                                                                                                                                                  | System prompt                                                                                                                                                                                       |
| `max_tokens`                                                                                                                                                                                        | *Optional[int]*                                                                                                                                                                                     | :heavy_minus_sign:                                                                                                                                                                                  | Maximum number of output tokens (optional).<br/>If not provided, the relay service or API may use a default value.<br/>Different models have different maximum values.<br/>                         |
| `stop_sequences`                                                                                                                                                                                    | List[*str*]                                                                                                                                                                                         | :heavy_minus_sign:                                                                                                                                                                                  | Stop sequences                                                                                                                                                                                      |
| `stream`                                                                                                                                                                                            | *Optional[bool]*                                                                                                                                                                                    | :heavy_minus_sign:                                                                                                                                                                                  | N/A                                                                                                                                                                                                 |
| `temperature`                                                                                                                                                                                       | *Optional[float]*                                                                                                                                                                                   | :heavy_minus_sign:                                                                                                                                                                                  | N/A                                                                                                                                                                                                 |
| `top_p`                                                                                                                                                                                             | *Optional[float]*                                                                                                                                                                                   | :heavy_minus_sign:                                                                                                                                                                                  | N/A                                                                                                                                                                                                 |
| `top_k`                                                                                                                                                                                             | *Optional[int]*                                                                                                                                                                                     | :heavy_minus_sign:                                                                                                                                                                                  | Top-k sampling parameter. Only sample from the top K options for each subsequent token.                                                                                                             |
| `tools`                                                                                                                                                                                             | List[[models.AnthropicTool](../../models/anthropictool.md)]                                                                                                                                         | :heavy_minus_sign:                                                                                                                                                                                  | N/A                                                                                                                                                                                                 |
| `tool_choice`                                                                                                                                                                                       | [Optional[models.AnthropicMessageRequestToolChoice]](../../models/anthropicmessagerequesttoolchoice.md)                                                                                             | :heavy_minus_sign:                                                                                                                                                                                  | N/A                                                                                                                                                                                                 |
| `metadata`                                                                                                                                                                                          | Dict[str, *Any*]                                                                                                                                                                                    | :heavy_minus_sign:                                                                                                                                                                                  | An object describing metadata about the request. Can be used for tracking, identification, or filtering purposes.<br/>Common use cases: user_id, session_id, request_id, etc.<br/>                  |
| `thinking`                                                                                                                                                                                          | [Optional[models.Thinking]](../../models/thinking.md)                                                                                                                                               | :heavy_minus_sign:                                                                                                                                                                                  | Configuration for extended thinking (Claude 3.7+). When enabled, the model will spend more time thinking before responding.<br/>                                                                    |
| `service_tier`                                                                                                                                                                                      | [Optional[models.AnthropicMessageRequestServiceTier]](../../models/anthropicmessagerequestservicetier.md)                                                                                           | :heavy_minus_sign:                                                                                                                                                                                  | Service tier for request processing:<br/>- auto: Automatically select between standard and priority capacity<br/>- standard_only: Only use standard capacity (may have longer wait times during high load)<br/> |
| `retries`                                                                                                                                                                                           | [Optional[utils.RetryConfig]](../../models/utils/retryconfig.md)                                                                                                                                    | :heavy_minus_sign:                                                                                                                                                                                  | Configuration to override the default retry behavior of the client.                                                                                                                                 |

### Response

**[models.CreateMessageResponse](../../models/createmessageresponse.md)**

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