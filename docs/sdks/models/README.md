# Models
(*models*)

## Overview

### Available Operations

* [list](#list) - List available models
* [retrieve](#retrieve) - Retrieve model details

## list

List all available models

### Example Usage

<!-- UsageSnippet language="python" operationID="listModels" method="get" path="/models" -->
```python
from r9s import R9S


with R9S(
    api_key="<YOUR_BEARER_TOKEN_HERE>",
) as r9_s:

    res = r9_s.models.list()

    # Handle response
    print(res)

```

### Parameters

| Parameter                                                           | Type                                                                | Required                                                            | Description                                                         |
| ------------------------------------------------------------------- | ------------------------------------------------------------------- | ------------------------------------------------------------------- | ------------------------------------------------------------------- |
| `retries`                                                           | [Optional[utils.RetryConfig]](../../models/utils/retryconfig.md)    | :heavy_minus_sign:                                                  | Configuration to override the default retry behavior of the client. |

### Response

**[models.ModelListResponse](../../models/modellistresponse.md)**

### Errors

| Error Type                   | Status Code                  | Content Type                 |
| ---------------------------- | ---------------------------- | ---------------------------- |
| errors.AuthenticationError   | 401                          | application/json             |
| errors.PermissionDeniedError | 403                          | application/json             |
| errors.InternalServerError   | 500                          | application/json             |
| errors.R9SDefaultError       | 4XX, 5XX                     | \*/\*                        |

## retrieve

Retrieve detailed information for a specified model

### Example Usage

<!-- UsageSnippet language="python" operationID="retrieveModel" method="get" path="/models/{model}" -->
```python
from r9s import R9S


with R9S(
    api_key="<YOUR_BEARER_TOKEN_HERE>",
) as r9_s:

    res = r9_s.models.retrieve(model="gpt-4o-mini")

    # Handle response
    print(res)

```

### Parameters

| Parameter                                                           | Type                                                                | Required                                                            | Description                                                         | Example                                                             |
| ------------------------------------------------------------------- | ------------------------------------------------------------------- | ------------------------------------------------------------------- | ------------------------------------------------------------------- | ------------------------------------------------------------------- |
| `model`                                                             | *str*                                                               | :heavy_check_mark:                                                  | Model name                                                          | gpt-4o-mini                                                         |
| `retries`                                                           | [Optional[utils.RetryConfig]](../../models/utils/retryconfig.md)    | :heavy_minus_sign:                                                  | Configuration to override the default retry behavior of the client. |                                                                     |

### Response

**[models.Model](../../models/model.md)**

### Errors

| Error Type                   | Status Code                  | Content Type                 |
| ---------------------------- | ---------------------------- | ---------------------------- |
| errors.AuthenticationError   | 401                          | application/json             |
| errors.PermissionDeniedError | 403                          | application/json             |
| errors.NotFoundError         | 404                          | application/json             |
| errors.InternalServerError   | 500                          | application/json             |
| errors.R9SDefaultError       | 4XX, 5XX                     | \*/\*                        |