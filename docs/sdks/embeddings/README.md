# Embeddings
(*embeddings*)

## Overview

### Available Operations

* [create](#create) - Create embeddings

## create

Create embedding vector representations for input text

### Example Usage

<!-- UsageSnippet language="python" operationID="createEmbedding" method="post" path="/embeddings" -->
```python
from r9s import R9S


with R9S(
    api_key="<YOUR_BEARER_TOKEN_HERE>",
) as r9_s:

    res = r9_s.embeddings.create(model="qwen-plus", input="The food was delicious and the waiter was friendly.", encoding_format="float")

    # Handle response
    print(res)

```

### Parameters

| Parameter                                                             | Type                                                                  | Required                                                              | Description                                                           |
| --------------------------------------------------------------------- | --------------------------------------------------------------------- | --------------------------------------------------------------------- | --------------------------------------------------------------------- |
| `model`                                                               | *str*                                                                 | :heavy_check_mark:                                                    | Model name                                                            |
| `input`                                                               | [models.EmbeddingRequestInput](../../models/embeddingrequestinput.md) | :heavy_check_mark:                                                    | Input text                                                            |
| `encoding_format`                                                     | [Optional[models.EncodingFormat]](../../models/encodingformat.md)     | :heavy_minus_sign:                                                    | N/A                                                                   |
| `dimensions`                                                          | *Optional[int]*                                                       | :heavy_minus_sign:                                                    | Output dimensions                                                     |
| `user`                                                                | *Optional[str]*                                                       | :heavy_minus_sign:                                                    | N/A                                                                   |
| `retries`                                                             | [Optional[utils.RetryConfig]](../../models/utils/retryconfig.md)      | :heavy_minus_sign:                                                    | Configuration to override the default retry behavior of the client.   |

### Response

**[models.EmbeddingResponse](../../models/embeddingresponse.md)**

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