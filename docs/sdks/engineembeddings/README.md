# EngineEmbeddings
(*engine_embeddings*)

## Overview

### Available Operations

* [create](#create) - Create engine embeddings

## create

Create embedding vectors for input text using specified engine

### Example Usage

<!-- UsageSnippet language="python" operationID="createEngineEmbedding" method="post" path="/engines/{model}/embeddings" -->
```python
from r9s import R9S


with R9S(
    api_key="<YOUR_BEARER_TOKEN_HERE>",
) as r9_s:

    res = r9_s.engine_embeddings.create(model="qwen-plus", input="The quick brown fox jumps over the lazy dog", encoding_format="float")

    # Handle response
    print(res)

```

### Parameters

| Parameter                                                                                                     | Type                                                                                                          | Required                                                                                                      | Description                                                                                                   | Example                                                                                                       |
| ------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------- |
| `model`                                                                                                       | *str*                                                                                                         | :heavy_check_mark:                                                                                            | Engine model name                                                                                             | qwen-plus                                                                                                     |
| `input`                                                                                                       | [models.EngineEmbeddingRequestInput](../../models/engineembeddingrequestinput.md)                             | :heavy_check_mark:                                                                                            | Input text                                                                                                    |                                                                                                               |
| `encoding_format`                                                                                             | [Optional[models.EngineEmbeddingRequestEncodingFormat]](../../models/engineembeddingrequestencodingformat.md) | :heavy_minus_sign:                                                                                            | N/A                                                                                                           |                                                                                                               |
| `dimensions`                                                                                                  | *Optional[int]*                                                                                               | :heavy_minus_sign:                                                                                            | Output dimensions                                                                                             |                                                                                                               |
| `user`                                                                                                        | *Optional[str]*                                                                                               | :heavy_minus_sign:                                                                                            | N/A                                                                                                           |                                                                                                               |
| `retries`                                                                                                     | [Optional[utils.RetryConfig]](../../models/utils/retryconfig.md)                                              | :heavy_minus_sign:                                                                                            | Configuration to override the default retry behavior of the client.                                           |                                                                                                               |

### Response

**[models.EmbeddingResponse](../../models/embeddingresponse.md)**

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