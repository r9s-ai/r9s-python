# Images
(*images*)

## Overview

### Available Operations

* [create](#create) - Create image
* [edit](#edit) - Edit image

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

## edit

Edit an existing image using a text prompt (inpainting). You can optionally provide a mask to specify which areas of the image should be edited.

### Example Usage

```python
from r9s import R9S


with R9S(
    api_key="<YOUR_BEARER_TOKEN_HERE>",
) as client:
    # Read the image file
    with open("original.png", "rb") as f:
        image_data = f.read()

    # Basic image edit
    res = client.images.edit(
        image={"file_name": "original.png", "content": image_data},
        prompt="Add a red hat to the person",
        model="dall-e-2",
        size="1024x1024"
    )

    print(res.data[0].url)
```

### Example with Mask (Inpainting)

```python
from r9s import R9S


with R9S(
    api_key="<YOUR_BEARER_TOKEN_HERE>",
) as client:
    with open("photo.png", "rb") as img, open("mask.png", "rb") as msk:
        res = client.images.edit(
            image={"file_name": "photo.png", "content": img.read()},
            mask={"file_name": "mask.png", "content": msk.read()},
            prompt="Replace the background with a beach sunset",
            n=2,
            response_format="b64_json"
        )

    # Save the edited images
    import base64
    for i, img in enumerate(res.data):
        data = base64.b64decode(img.b64_json)
        with open(f"result_{i}.png", "wb") as f:
            f.write(data)
```

### Async Example

```python
import asyncio
from r9s import R9S


async def edit_image():
    async with R9S(api_key="<YOUR_BEARER_TOKEN_HERE>") as client:
        with open("input.png", "rb") as f:
            res = await client.images.edit_async(
                image={"file_name": "input.png", "content": f.read()},
                prompt="Make it look like a watercolor painting"
            )
        return res.data[0].url

url = asyncio.run(edit_image())
print(url)
```

### Parameters

| Parameter                                                                           | Type                                                                                | Required                                                                            | Description                                                                         |
| ----------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------- |
| `image`                                                                             | [models.ImageFile](../../models/imagefile.md)                                       | :heavy_check_mark:                                                                  | The image to edit. Must be PNG format, less than 4MB, and square.                   |
| `prompt`                                                                            | *str*                                                                               | :heavy_check_mark:                                                                  | A text description of the desired edit or result. Max 1000 characters.              |
| `model`                                                                             | *Optional[str]*                                                                     | :heavy_minus_sign:                                                                  | Model identifier (e.g., "dall-e-2")                                                 |
| `mask`                                                                              | [Optional[models.ImageFile]](../../models/imagefile.md)                             | :heavy_minus_sign:                                                                  | PNG with transparent areas indicating where to edit. Must match image dimensions.   |
| `n`                                                                                 | *Optional[int]*                                                                     | :heavy_minus_sign:                                                                  | Number of images to generate. Range: 1-10. Default: 1                               |
| `size`                                                                              | [Optional[models.ImageEditSize]](../../models/imageeditsize.md)                     | :heavy_minus_sign:                                                                  | Output size: "256x256", "512x512", or "1024x1024" (default)                         |
| `response_format`                                                                   | [Optional[models.ImageEditResponseFormat]](../../models/imageeditresponseformat.md) | :heavy_minus_sign:                                                                  | Format of returned images: "url" (default) or "b64_json"                            |
| `user`                                                                              | *Optional[str]*                                                                     | :heavy_minus_sign:                                                                  | Unique identifier for end-user tracking                                             |
| `retries`                                                                           | [Optional[utils.RetryConfig]](../../models/utils/retryconfig.md)                    | :heavy_minus_sign:                                                                  | Configuration to override the default retry behavior of the client.                 |

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