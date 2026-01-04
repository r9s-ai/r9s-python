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
| `negative_prompt`                                                                                             | *Optional[str]*                                                                                               | :heavy_minus_sign:                                                                                            | Negative prompt to exclude elements (Qwen, Stability)                                                         |
| `seed`                                                                                                        | *Optional[int]*                                                                                               | :heavy_minus_sign:                                                                                            | Random seed for reproducibility                                                                               |
| `prompt_extend`                                                                                               | *Optional[bool]*                                                                                              | :heavy_minus_sign:                                                                                            | Enable AI prompt optimization (Qwen-specific)                                                                 |
| `watermark`                                                                                                   | *Optional[bool]*                                                                                              | :heavy_minus_sign:                                                                                            | Add watermark to generated images (Qwen-specific)                                                             |
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

---

## Extended Parameters

Some providers support additional parameters beyond the OpenAI standard:

### GPT-Image-1.5 (Multiple Images)

Generate multiple images in a single request with gpt-image-1.5:

```python
from r9s import R9S


with R9S(api_key="<YOUR_BEARER_TOKEN_HERE>") as client:
    # Generate 5 images at once (only gpt-image-1.5 supports n>1)
    result = client.images.create(
        prompt="A futuristic electric car in a showroom",
        model="gpt-image-1.5",
        n=5,                    # 1-10 images supported
        size="1536x1024",       # Landscape
        quality="high"
    )

    # Access all generated images
    for i, image in enumerate(result.data):
        print(f"Image {i+1}: {image.url}")
```

### Negative Prompt (Qwen, Stability)

Specify elements to exclude from the generated image:

```python
from r9s import R9S


with R9S(api_key="<YOUR_BEARER_TOKEN_HERE>") as client:
    result = client.images.create(
        prompt="A serene mountain landscape",
        negative_prompt="people, buildings, cars",
        model="wanx-v1"
    )
```

### Seed (Reproducibility)

Generate consistent results with the same seed:

```python
from r9s import R9S


with R9S(api_key="<YOUR_BEARER_TOKEN_HERE>") as client:
    result = client.images.create(
        prompt="A blue dragon",
        seed=12345,
        model="wanx-v1"
    )
```

### Gemini Nano Banana (Aspect Ratios)

Use aspect ratios for precise image dimensions:

```python
from r9s import R9S


with R9S(api_key="<YOUR_BEARER_TOKEN_HERE>") as client:
    # Using aspect ratio directly
    result = client.images.create(
        prompt="A futuristic cityscape at sunset",
        model="gemini-2.5-flash-image",
        size="16:9",        # Landscape aspect ratio
        quality="hd"        # Maps to 2K resolution
    )

    # Using pixel dimensions (mapped to aspect ratio)
    result = client.images.create(
        prompt="A portrait of a cyberpunk character",
        model="gemini-2.5-flash-image",
        size="1024x1792",   # Automatically mapped to 9:16
    )

    # 4K resolution with Nano Banana Pro
    result = client.images.create(
        prompt="Ultra-detailed landscape",
        model="gemini-3-pro-image-preview",
        size="1:1",
        quality="4k"        # Only available on Pro model
    )
```

### Provider-Specific Constraints

| Provider | Prompt Max | N Range | Special |
|----------|------------|---------|---------|
| OpenAI DALL-E 2 | 1000 | 1-10 | Legacy model |
| OpenAI DALL-E 3 | 4000 | 1 | High quality |
| OpenAI gpt-image-1 | 4000 | 1 | |
| OpenAI gpt-image-1.5 | 4000 | 1-10 | 4x faster, 20% cheaper |
| Gemini Nano Banana | 32000 | 1 | aspect_ratio, quality->resolution |
| Gemini Nano Banana Pro | 32000 | 1 | aspect_ratio, 4K support |
| Qwen/Wanx | 800 | 1 | negative_prompt, seed |
| Minimax | 1500 | 1-9 | aspect_ratio |
| CogView | 833 | 1 | |

### Using Image Constraints Helper

The SDK provides a utility module for validating image requests against provider constraints:

```python
from r9s.utils.image_constraints import (
    get_model_constraints,
    validate_image_request,
)


# Get constraints for a model
constraints = get_model_constraints("wanx-v1")
print(f"Max prompt length: {constraints.prompt_max}")
print(f"Supports negative_prompt: {constraints.supports_negative_prompt}")

# Validate a request before sending
errors = validate_image_request(
    model="wanx-v1",
    prompt="A very long prompt...",
    size="1024x1024",
    n=1
)
if errors:
    print("Validation errors:", errors)
```