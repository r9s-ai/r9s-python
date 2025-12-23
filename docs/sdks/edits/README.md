# Edits
(*edits*)

## Overview

### Available Operations

* [create](#create) - Create text edit

## create

Edit given text according to instructions

### Example Usage

<!-- UsageSnippet language="python" operationID="createEdit" method="post" path="/edits" -->
```python
from r9s import R9S


with R9S(
    api_key="<YOUR_BEARER_TOKEN_HERE>",
) as r9_s:

    res = r9_s.edits.create(model="gpt-4o-mini", instruction="Fix the spelling mistakes", input="What day of the wek is it?", n=1, temperature=1, top_p=1)

    # Handle response
    print(res)

```

### Parameters

| Parameter                                                           | Type                                                                | Required                                                            | Description                                                         |
| ------------------------------------------------------------------- | ------------------------------------------------------------------- | ------------------------------------------------------------------- | ------------------------------------------------------------------- |
| `model`                                                             | *str*                                                               | :heavy_check_mark:                                                  | Model name                                                          |
| `instruction`                                                       | *str*                                                               | :heavy_check_mark:                                                  | Edit instruction                                                    |
| `input`                                                             | *Optional[str]*                                                     | :heavy_minus_sign:                                                  | Input text to edit                                                  |
| `n`                                                                 | *Optional[int]*                                                     | :heavy_minus_sign:                                                  | N/A                                                                 |
| `temperature`                                                       | *Optional[float]*                                                   | :heavy_minus_sign:                                                  | N/A                                                                 |
| `top_p`                                                             | *Optional[float]*                                                   | :heavy_minus_sign:                                                  | N/A                                                                 |
| `retries`                                                           | [Optional[utils.RetryConfig]](../../models/utils/retryconfig.md)    | :heavy_minus_sign:                                                  | Configuration to override the default retry behavior of the client. |

### Response

**[models.EditResponse](../../models/editresponse.md)**

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