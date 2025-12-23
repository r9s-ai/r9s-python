# Moderations
(*moderations*)

## Overview

### Available Operations

* [create](#create) - Create content moderation

## create

Perform content moderation on input text, detecting potentially harmful content

### Example Usage

<!-- UsageSnippet language="python" operationID="createModeration" method="post" path="/moderations" -->
```python
from r9s import R9S


with R9S(
    api_key="<YOUR_BEARER_TOKEN_HERE>",
) as r9_s:

    res = r9_s.moderations.create(input="I want to hurt someone", model="gpt-4o-mini")

    # Handle response
    print(res)

```

### Parameters

| Parameter                                                               | Type                                                                    | Required                                                                | Description                                                             |
| ----------------------------------------------------------------------- | ----------------------------------------------------------------------- | ----------------------------------------------------------------------- | ----------------------------------------------------------------------- |
| `input`                                                                 | [models.ModerationRequestInput](../../models/moderationrequestinput.md) | :heavy_check_mark:                                                      | Input text to moderate                                                  |
| `model`                                                                 | *Optional[str]*                                                         | :heavy_minus_sign:                                                      | Model name                                                              |
| `retries`                                                               | [Optional[utils.RetryConfig]](../../models/utils/retryconfig.md)        | :heavy_minus_sign:                                                      | Configuration to override the default retry behavior of the client.     |

### Response

**[models.ModerationResponse](../../models/moderationresponse.md)**

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