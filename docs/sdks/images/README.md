# Images
(*images*)

## Overview

### Available Operations

* [create](#create) - Create image

## create

Generate images from text prompts

### Example Usage

<!-- UsageSnippet language="python" operationID="createImageGeneration" method="post" path="/images/generations" -->
```python
from r9s import R9S


with R9S(
    api_key="<YOUR_BEARER_TOKEN_HERE>",
) as r9_s:

    res = r9_s.images.create(prompt="A cute cat sitting on a windowsill", model="gpt-4o-mini", n=1, quality="standard", response_format="url", size="1024x1024", style="vivid")

    # Handle response
    print(res)

```

### Parameters

| Parameter                                                                                                     | Type                                                                                                          | Required                                                                                                      | Description                                                                                                   |
| ------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------- |
| `prompt`                                                                                                      | *str*                                                                                                         | :heavy_check_mark:                                                                                            | Image description prompt                                                                                      |
| `model`                                                                                                       | *Optional[str]*                                                                                               | :heavy_minus_sign:                                                                                            | Model name                                                                                                    |
| `n`                                                                                                           | *Optional[int]*                                                                                               | :heavy_minus_sign:                                                                                            | Number of images to generate                                                                                  |
| `quality`                                                                                                     | [Optional[models.Quality]](../../models/quality.md)                                                           | :heavy_minus_sign:                                                                                            | N/A                                                                                                           |
| `response_format`                                                                                             | [Optional[models.ImageGenerationRequestResponseFormat]](../../models/imagegenerationrequestresponseformat.md) | :heavy_minus_sign:                                                                                            | N/A                                                                                                           |
| `size`                                                                                                        | [Optional[models.Size]](../../models/size.md)                                                                 | :heavy_minus_sign:                                                                                            | N/A                                                                                                           |
| `style`                                                                                                       | [Optional[models.Style]](../../models/style.md)                                                               | :heavy_minus_sign:                                                                                            | N/A                                                                                                           |
| `user`                                                                                                        | *Optional[str]*                                                                                               | :heavy_minus_sign:                                                                                            | N/A                                                                                                           |
| `retries`                                                                                                     | [Optional[utils.RetryConfig]](../../models/utils/retryconfig.md)                                              | :heavy_minus_sign:                                                                                            | Configuration to override the default retry behavior of the client.                                           |

### Response

**[models.ImageGenerationResponse](../../models/imagegenerationresponse.md)**

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