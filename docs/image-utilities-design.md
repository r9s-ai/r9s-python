# Image Utilities – High-Level Design

This document describes the architecture and design of image-related utilities in the r9s Python SDK, including image generation, image editing, and vision input support.

## Overview

The r9s SDK provides image utilities through a layered architecture:

```
┌─────────────────────────────────────────────────────────────────────┐
│                         r9s Python SDK                              │
├─────────────────────────────────────────────────────────────────────┤
│  Images API      │  Edits API       │  Vision Input (Chat/Messages) │
│  (images.py)     │  (edits.py)      │  (Anthropic models)           │
├─────────────────────────────────────────────────────────────────────┤
│                         BaseSDK                                     │
│            (HTTP client, auth, retry, error handling)               │
├─────────────────────────────────────────────────────────────────────┤
│                    AI Gateway (next-router)                         │
│              /v1/images/generations  │  /v1/images/edits            │
├─────────────────────────────────────────────────────────────────────┤
│                      Provider Adaptor Layer                         │
│    OpenAI  │  Alibaba  │  Anthropic  │  Stability  │  42+ others   │
└─────────────────────────────────────────────────────────────────────┘
```

## Components

### 1. Image Generation (`r9s.images`)

**Module:** `src/r9s/images.py`

**Purpose:** Generate images from text prompts using AI models.

**Class:** `Images(BaseSDK)`

#### Methods

| Method | Description |
|--------|-------------|
| `create()` | Synchronous image generation |
| `create_async()` | Asynchronous image generation |

#### Request Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `prompt` | `str` | Required | Image description prompt |
| `model` | `Optional[str]` | None | Model identifier |
| `n` | `Optional[int]` | 1 | Number of images to generate |
| `quality` | `Quality` | "standard" | "standard" or "hd" |
| `response_format` | `ResponseFormat` | "url" | "url" or "b64_json" |
| `size` | `Size` | "1024x1024" | Output dimensions |
| `style` | `Style` | "vivid" | "vivid" or "natural" |
| `user` | `Optional[str]` | None | User identifier for tracking |

#### Supported Sizes

- `256x256`
- `512x512`
- `1024x1024` (default)
- `1792x1024` (landscape)
- `1024x1792` (portrait)

#### Response Flow

```
SDK Request
    │
    ▼
POST /images/generations
    │
    ▼
Gateway Routes to Provider
    │
    ▼
ImageGenerationResponse
├── created: int (timestamp)
└── data: List[ImageObject]
    ├── url: Optional[str]
    ├── b64_json: Optional[str]
    └── revised_prompt: Optional[str]
```

---

### 2. Text Editing (`r9s.edits`)

**Module:** `src/r9s/edits.py`

**Purpose:** Edit text according to natural language instructions.

**Class:** `Edits(BaseSDK)`

#### Methods

| Method | Description |
|--------|-------------|
| `create()` | Synchronous text editing |
| `create_async()` | Asynchronous text editing |

#### Request Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `model` | `str` | Required | Model identifier |
| `instruction` | `str` | Required | Edit instruction |
| `input` | `Optional[str]` | "" | Input text to edit |
| `n` | `Optional[int]` | 1 | Number of edits to generate |
| `temperature` | `Optional[float]` | 1.0 | Sampling temperature |
| `top_p` | `Optional[float]` | 1.0 | Nucleus sampling parameter |

#### Response Flow

```
SDK Request
    │
    ▼
POST /edits
    │
    ▼
Gateway Routes to Provider
    │
    ▼
EditResponse
├── object: str
├── created: int
├── choices: List[EditChoice]
│   ├── text: str
│   └── index: int
└── usage: Usage
```

---

### 3. Vision Input (Multimodal Chat)

**Purpose:** Send images as input to vision-capable models for understanding and analysis.

#### Anthropic Image Models

| Model | File | Purpose |
|-------|------|---------|
| `AnthropicImageContent` | `anthropicimagecontent.py` | Image content wrapper for messages |
| `AnthropicImageSource` | `anthropicimagesource.py` | Discriminated union for image sources |
| `AnthropicImageSourceBase64` | `anthropicimagesourcebase64.py` | Base64-encoded image data |
| `AnthropicImageSourceURL` | `anthropicimagesourceurl.py` | URL-based image reference |

#### Image Source Types

**Base64 Source:**
```python
{
    "type": "base64",
    "media_type": "image/png",  # jpeg, png, gif, webp
    "data": "<base64-encoded-data>"
}
```

**URL Source:**
```python
{
    "type": "url",
    "url": "https://example.com/image.jpg"
}
```

#### OpenAI-Style Vision Input

For chat completions, images can be passed using the OpenAI format:

```python
{
    "type": "image_url",
    "image_url": {
        "url": "https://example.com/image.jpg",
        "detail": "auto"  # auto, low, high
    }
}
```

---

### 4. CLI Image Processing

**Module:** `src/r9s/cli_tools/chat_cli.py`

**Purpose:** Handle piped image input in the CLI.

#### Image Detection

The CLI detects image formats by magic bytes:

| Format | Magic Bytes |
|--------|-------------|
| PNG | `\x89PNG\r\n\x1a\n` |
| JPEG | `\xff\xd8\xff` |
| GIF | `GIF87a` or `GIF89a` |
| WebP | `RIFF...WEBP` |

#### Processing Flow

```
Piped Input (stdin)
    │
    ▼
_detect_image_mime(data)
    │
    ├── Image detected → Create data URL (base64)
    │                    Default prompt: "Describe this image."
    │
    └── Text detected → Parse as text message
```

#### Constraints

- Maximum image size: 10MB
- Supported formats: PNG, JPEG, GIF, WebP

---

## Data Models

### Image Generation Models

| Model | File | Purpose |
|-------|------|---------|
| `ImageGenerationRequest` | `imagegenerationrequest.py` | Request payload |
| `ImageGenerationResponse` | `imagegenerationresponse.py` | Response envelope |
| `ImageObject` | `imageobject.py` | Individual generated image |
| `ImageURL` | `imageurl.py` | Image URL with detail level |
| `Quality` | `imagegenerationrequest.py` | "standard" \| "hd" |
| `Size` | `imagegenerationrequest.py` | Image dimensions |
| `Style` | `imagegenerationrequest.py` | "vivid" \| "natural" |

### Edit Models

| Model | File | Purpose |
|-------|------|---------|
| `EditRequest` | `editrequest.py` | Request payload |
| `EditResponse` | `editresponse.py` | Response envelope |
| `EditChoice` | `editchoice.py` | Individual edit result |

---

## Gateway Integration

The SDK communicates with the AI Gateway (next-router), which provides:

### Endpoints

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/v1/images/generations` | POST | Image generation |
| `/v1/images/edits` | POST | Image editing |

### Gateway Features

1. **Provider Routing**: Routes requests to 42+ AI providers based on model configuration
2. **Request Transformation**: Converts OpenAI-format requests to provider-specific formats
3. **Response Normalization**: Returns consistent OpenAI-format responses regardless of provider
4. **Load Balancing**: Distributes requests across configured channels
5. **Billing**: Tracks usage and applies pricing based on model and operation

### Provider Support for Images

| Provider | Image Generation | Image Editing | Notes |
|----------|------------------|---------------|-------|
| OpenAI | DALL-E 2/3 | DALL-E 2 | Full support |
| Alibaba | Wanx | - | Converts to base64 if needed |
| Stability | Stable Diffusion | - | Via API |
| Others | Varies | Varies | Provider-dependent |

---

## Error Handling

All image utilities use consistent error handling:

| Status Code | Error Type | Description |
|-------------|------------|-------------|
| 400 | `BadRequestError` | Invalid request parameters |
| 401 | `AuthenticationError` | Invalid or missing API key |
| 403 | `PermissionDeniedError` | Access denied |
| 422 | `UnprocessableEntityError` | Validation failed |
| 429 | `RateLimitError` | Rate limit exceeded |
| 500 | `InternalServerError` | Server error |
| 503 | `ServiceUnavailableError` | Service temporarily unavailable |

### Retry Behavior

The SDK automatically retries on these status codes:
- `429` (Rate Limit)
- `500`, `502`, `503`, `504` (Server Errors)

Retry configuration can be overridden per-request via the `retries` parameter.

---

## Usage Examples

### Image Generation

```python
from r9s import R9S

with R9S(api_key="<API_KEY>") as client:
    # Basic generation
    result = client.images.create(
        prompt="A sunset over mountains",
        model="dall-e-3",
        size="1024x1024"
    )

    # HD quality with natural style
    result = client.images.create(
        prompt="A photorealistic portrait",
        quality="hd",
        style="natural",
        response_format="b64_json"
    )

    print(result.data[0].url)
```

### Async Image Generation

```python
import asyncio
from r9s import R9S

async def generate_images():
    async with R9S(api_key="<API_KEY>") as client:
        result = await client.images.create_async(
            prompt="A futuristic city",
            n=4
        )
        return result.data

images = asyncio.run(generate_images())
```

### Text Editing

```python
from r9s import R9S

with R9S(api_key="<API_KEY>") as client:
    result = client.edits.create(
        model="gpt-4o-mini",
        instruction="Fix grammar and spelling",
        input="I has went to the store yesterday"
    )

    print(result.choices[0].text)
```

### Vision Input (Chat)

```python
from r9s import R9S

with R9S(api_key="<API_KEY>") as client:
    result = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": "What's in this image?"},
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": "https://example.com/image.jpg",
                            "detail": "high"
                        }
                    }
                ]
            }
        ]
    )
```

---

## File Structure

```
src/r9s/
├── images.py                    # Image generation SDK
├── edits.py                     # Text editing SDK
├── sdk.py                       # Main SDK (lazy-loads images, edits)
├── models/
│   ├── imagegenerationrequest.py
│   ├── imagegenerationresponse.py
│   ├── imageobject.py
│   ├── imageurl.py
│   ├── editrequest.py
│   ├── editresponse.py
│   ├── editchoice.py
│   ├── anthropicimagecontent.py
│   ├── anthropicimagesource.py
│   ├── anthropicimagesourcebase64.py
│   └── anthropicimagesourceurl.py
└── cli_tools/
    └── chat_cli.py              # CLI image detection/processing

docs/
├── sdks/
│   ├── images/README.md         # Images API reference
│   └── edits/README.md          # Edits API reference
└── models/
    ├── imagegenerationrequest.md
    ├── imagegenerationresponse.md
    └── ...
```

---

## Design Decisions

### 1. OpenAI API Compatibility

The SDK follows the OpenAI API specification for maximum compatibility. This allows:
- Easy migration from OpenAI SDK
- Consistent developer experience across providers
- Gateway handles provider-specific transformations

### 2. Sync/Async Duality

Every operation has both synchronous and asynchronous variants:
- `create()` for synchronous code
- `create_async()` for asyncio-based applications

### 3. Lazy Loading

Sub-SDKs (`images`, `edits`) are lazy-loaded to reduce import time and memory footprint when not used.

### 4. Code Generation

The SDK is generated from OpenAPI specifications using Speakeasy, ensuring:
- Consistency with API contract
- Automatic updates when API changes
- Type safety via Pydantic models

---

## Implementation Spec: Image Editing (Inpainting)

> **STATUS: NOT IMPLEMENTED** - This section provides complete specifications for implementing image editing support.

### Gap Analysis

| Feature | Gateway Support | SDK Support | Priority |
|---------|-----------------|-------------|----------|
| Image Generation | `POST /v1/images/generations` | `images.create()` | Done |
| **Image Editing** | `POST /v1/images/edits` | **Missing** | **HIGH** |
| Image Variations | Not in gateway | N/A | N/A |

### API Endpoint Specification

**Endpoint:** `POST /v1/images/edits`

**Content-Type:** `multipart/form-data`

**Purpose:** Edit or extend an existing image using a text prompt. Supports inpainting (editing specific regions using a mask) and outpainting (extending the image).

### Request Fields

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `image` | `file` | **Yes** | - | The image to edit. Must be PNG format, less than 4MB, and square. |
| `prompt` | `string` | **Yes** | - | A text description of the desired edit or result. Max 1000 characters. |
| `model` | `string` | No | Provider default | Model identifier (e.g., "dall-e-2", "gpt-image-1") |
| `mask` | `file` | No | - | PNG file with transparent areas indicating where to edit. Must match image dimensions. |
| `n` | `integer` | No | `1` | Number of images to generate. Range: 1-10. |
| `size` | `string` | No | `"1024x1024"` | Output image size. |
| `response_format` | `string` | No | `"url"` | `"url"` or `"b64_json"` |
| `user` | `string` | No | - | Unique identifier for end-user tracking. |

### Supported Sizes (Image Edit)

| Size | Notes |
|------|-------|
| `256x256` | Fastest |
| `512x512` | Balanced |
| `1024x1024` | Default, best quality |

> Note: Unlike image generation, image editing does NOT support `1792x1024` or `1024x1792`.

### Response Format

The response uses the **same format as image generation**:

```json
{
  "created": 1699000000,
  "data": [
    {
      "url": "https://...",
      "b64_json": null,
      "revised_prompt": "A cat sitting on a windowsill with sunlight..."
    }
  ]
}
```

**Response Model:** Reuse existing `ImageGenerationResponse` (no new response model needed).

### Error Responses

| Status | Error Type | Common Causes |
|--------|------------|---------------|
| 400 | `BadRequestError` | Invalid image format, image too large, invalid size |
| 401 | `AuthenticationError` | Invalid API key |
| 403 | `PermissionDeniedError` | Access denied to model |
| 422 | `UnprocessableEntityError` | Prompt validation failed |
| 429 | `RateLimitError` | Too many requests |
| 500 | `InternalServerError` | Provider error |
| 503 | `ServiceUnavailableError` | Service temporarily unavailable |

### Provider Support

| Provider | Support | Models | Notes |
|----------|---------|--------|-------|
| OpenAI | Full | dall-e-2 | Original implementation |
| Azure OpenAI | Full | dall-e-2 | Via OpenAI adaptor |
| Anthropic | Yes | Claude vision models | ImagesEdit mode |
| Google Gemini | Yes | Imagen | Default validation |
| Alibaba (Qwen) | Yes | Wanx | ImagesEdit mode |
| Stability AI | Partial | SD models | Via adaptor |

---

### Implementation Guide

#### Files to Create

1. **`src/r9s/models/imageeditrequest.py`** - Request model for multipart form

#### Files to Modify

1. **`src/r9s/images.py`** - Add `edit()` and `edit_async()` methods
2. **`src/r9s/models/__init__.py`** - Export new models

---

### Model Implementation: `ImageEditRequest`

Create `src/r9s/models/imageeditrequest.py`:

```python
"""Image edit request model for inpainting operations."""

from __future__ import annotations
import io
import pydantic
from r9s.types import BaseModel
from r9s.utils import FieldMetadata, MultipartFormMetadata
from typing import IO, Literal, Optional, Union
from typing_extensions import Annotated, NotRequired, TypedDict


class ImageFileTypedDict(TypedDict):
    file_name: str
    content: Union[bytes, IO[bytes], io.BufferedReader]
    content_type: NotRequired[str]


class ImageFile(BaseModel):
    """Image file for upload."""

    file_name: Annotated[
        str, pydantic.Field(alias="fileName"), FieldMetadata(multipart=True)
    ]

    content: Annotated[
        Union[bytes, IO[bytes], io.BufferedReader],
        pydantic.Field(alias=""),
        FieldMetadata(multipart=MultipartFormMetadata(content=True)),
    ]

    content_type: Annotated[
        Optional[str],
        pydantic.Field(alias="Content-Type"),
        FieldMetadata(multipart=True),
    ] = None


ImageEditResponseFormat = Literal["url", "b64_json"]

ImageEditSize = Literal["256x256", "512x512", "1024x1024"]


class ImageEditRequestTypedDict(TypedDict):
    image: ImageFileTypedDict
    prompt: str
    model: NotRequired[str]
    mask: NotRequired[ImageFileTypedDict]
    n: NotRequired[int]
    size: NotRequired[ImageEditSize]
    response_format: NotRequired[ImageEditResponseFormat]
    user: NotRequired[str]


class ImageEditRequest(BaseModel):
    """Request model for image editing (inpainting) operations."""

    image: Annotated[
        ImageFile, FieldMetadata(multipart=MultipartFormMetadata(file=True))
    ]
    r"""The image to edit. Must be PNG, less than 4MB, and square."""

    prompt: Annotated[str, FieldMetadata(multipart=True)]
    r"""A text description of the desired image(s)."""

    model: Annotated[Optional[str], FieldMetadata(multipart=True)] = None
    r"""The model to use for image editing."""

    mask: Annotated[
        Optional[ImageFile],
        FieldMetadata(multipart=MultipartFormMetadata(file=True)),
    ] = None
    r"""PNG with transparent areas indicating where to edit."""

    n: Annotated[Optional[int], FieldMetadata(multipart=True)] = 1
    r"""Number of images to generate. Range: 1-10."""

    size: Annotated[Optional[ImageEditSize], FieldMetadata(multipart=True)] = (
        "1024x1024"
    )
    r"""The size of the generated images."""

    response_format: Annotated[
        Optional[ImageEditResponseFormat], FieldMetadata(multipart=True)
    ] = "url"
    r"""Format of returned images: 'url' or 'b64_json'."""

    user: Annotated[Optional[str], FieldMetadata(multipart=True)] = None
    r"""Unique identifier for end-user tracking."""
```

---

### SDK Implementation: Add to `images.py`

Add these methods to the `Images` class in `src/r9s/images.py`:

```python
def edit(
    self,
    *,
    image: Union[models.ImageFile, models.ImageFileTypedDict],
    prompt: str,
    model: Optional[str] = None,
    mask: Optional[Union[models.ImageFile, models.ImageFileTypedDict]] = None,
    n: Optional[int] = 1,
    size: Optional[models.ImageEditSize] = "1024x1024",
    response_format: Optional[models.ImageEditResponseFormat] = "url",
    user: Optional[str] = None,
    retries: OptionalNullable[utils.RetryConfig] = UNSET,
    server_url: Optional[str] = None,
    timeout_ms: Optional[int] = None,
    http_headers: Optional[Mapping[str, str]] = None,
) -> models.ImageGenerationResponse:
    r"""Edit image

    Edit an existing image using a text prompt (inpainting).

    :param image: The image to edit (PNG, <4MB, square)
    :param prompt: Text description of desired edit
    :param model: Model name
    :param mask: Optional mask PNG with transparent edit regions
    :param n: Number of images to generate (1-10)
    :param size: Output size
    :param response_format: 'url' or 'b64_json'
    :param user: End-user identifier
    :param retries: Override default retry configuration
    :param server_url: Override default server URL
    :param timeout_ms: Override default timeout in milliseconds
    :param http_headers: Additional headers
    """
    base_url = None
    url_variables = None
    if timeout_ms is None:
        timeout_ms = self.sdk_configuration.timeout_ms

    if server_url is not None:
        base_url = server_url
    else:
        base_url = self._get_url(base_url, url_variables)

    request = models.ImageEditRequest(
        image=utils.get_pydantic_model(image, models.ImageFile),
        prompt=prompt,
        model=model,
        mask=utils.get_pydantic_model(mask, models.ImageFile) if mask else None,
        n=n,
        size=size,
        response_format=response_format,
        user=user,
    )

    req = self._build_request(
        method="POST",
        path="/images/edits",
        base_url=base_url,
        url_variables=url_variables,
        request=request,
        request_body_required=True,
        request_has_path_params=False,
        request_has_query_params=True,
        user_agent_header="user-agent",
        accept_header_value="application/json",
        http_headers=http_headers,
        security=self.sdk_configuration.security,
        get_serialized_body=lambda: utils.serialize_request_body(
            request, False, False, "multipart", models.ImageEditRequest
        ),
        allow_empty_value=None,
        timeout_ms=timeout_ms,
    )

    if retries == UNSET:
        if self.sdk_configuration.retry_config is not UNSET:
            retries = self.sdk_configuration.retry_config

    retry_config = None
    if isinstance(retries, utils.RetryConfig):
        retry_config = (retries, ["429", "500", "502", "503", "504"])

    http_res = self.do_request(
        hook_ctx=HookContext(
            config=self.sdk_configuration,
            base_url=base_url or "",
            operation_id="editImage",
            oauth2_scopes=None,
            security_source=self.sdk_configuration.security,
        ),
        request=req,
        error_status_codes=[
            "400", "401", "403", "422", "429", "4XX", "500", "503", "5XX",
        ],
        retry_config=retry_config,
    )

    # Response handling (same as create())
    response_data: Any = None
    if utils.match_response(http_res, "200", "application/json"):
        return unmarshal_json_response(models.ImageGenerationResponse, http_res)
    # ... error handling same as create() method ...
```

**Key differences from `create()`:**

1. **Path:** `/images/edits` instead of `/images/generations`
2. **Serialization:** `"multipart"` instead of `"json"`
3. **Parameters:** `image` (file), `mask` (optional file) instead of just `prompt`
4. **Operation ID:** `"editImage"` for hooks

---

### Model Export: Update `models/__init__.py`

Add to the `TYPE_CHECKING` imports:

```python
from .imageeditrequest import (
    ImageEditRequest,
    ImageEditRequestTypedDict,
    ImageEditResponseFormat,
    ImageEditSize,
    ImageFile,
    ImageFileTypedDict,
)
```

Add to `__all__`:

```python
"ImageEditRequest",
"ImageEditRequestTypedDict",
"ImageEditResponseFormat",
"ImageEditSize",
"ImageFile",
"ImageFileTypedDict",
```

Add to `_dynamic_imports`:

```python
"ImageEditRequest": ".imageeditrequest",
"ImageEditRequestTypedDict": ".imageeditrequest",
"ImageEditResponseFormat": ".imageeditrequest",
"ImageEditSize": ".imageeditrequest",
"ImageFile": ".imageeditrequest",
"ImageFileTypedDict": ".imageeditrequest",
```

---

### Usage Examples

#### Basic Image Edit

```python
from r9s import R9S

with R9S(api_key="<API_KEY>") as client:
    # Read image file
    with open("original.png", "rb") as f:
        image_data = f.read()

    result = client.images.edit(
        image={"file_name": "original.png", "content": image_data},
        prompt="Add a red hat to the person",
        model="dall-e-2",
        size="1024x1024"
    )

    print(result.data[0].url)
```

#### Inpainting with Mask

```python
from r9s import R9S

with R9S(api_key="<API_KEY>") as client:
    with open("photo.png", "rb") as img, open("mask.png", "rb") as msk:
        result = client.images.edit(
            image={"file_name": "photo.png", "content": img.read()},
            mask={"file_name": "mask.png", "content": msk.read()},
            prompt="Replace the background with a beach sunset",
            n=2,
            response_format="b64_json"
        )

    for i, img in enumerate(result.data):
        # Save base64 images
        import base64
        data = base64.b64decode(img.b64_json)
        with open(f"result_{i}.png", "wb") as f:
            f.write(data)
```

#### Async Edit

```python
import asyncio
from r9s import R9S

async def edit_image():
    async with R9S(api_key="<API_KEY>") as client:
        with open("input.png", "rb") as f:
            result = await client.images.edit_async(
                image={"file_name": "input.png", "content": f.read()},
                prompt="Make it look like a watercolor painting"
            )
        return result.data[0].url

url = asyncio.run(edit_image())
```

---

### Test Specifications

Create `tests/test_image_edit.py`:

#### Test Dependencies

```python
from __future__ import annotations

import base64
import io
import json
from typing import Any, Optional
from unittest.mock import MagicMock, patch

import httpx
import pytest

from r9s import R9S, models
from r9s.models.imageeditrequest import (
    ImageEditRequest,
    ImageEditSize,
    ImageEditResponseFormat,
    ImageFile,
    ImageFileTypedDict,
)
```

---

#### 1. Model Unit Tests

```python
class TestImageFileModel:
    """Tests for ImageFile model."""

    def test_image_file_with_bytes(self) -> None:
        """ImageFile accepts bytes content."""
        png_bytes = b"\x89PNG\r\n\x1a\n" + b"\x00" * 100
        file = ImageFile(
            file_name="test.png",
            content=png_bytes,
            content_type="image/png",
        )
        assert file.file_name == "test.png"
        assert file.content == png_bytes
        assert file.content_type == "image/png"

    def test_image_file_with_io_bytes(self) -> None:
        """ImageFile accepts IO[bytes] content."""
        png_bytes = b"\x89PNG\r\n\x1a\n" + b"\x00" * 100
        buffer = io.BytesIO(png_bytes)
        file = ImageFile(
            file_name="test.png",
            content=buffer,
        )
        assert file.file_name == "test.png"
        assert file.content_type is None  # Optional

    def test_image_file_from_typed_dict(self) -> None:
        """ImageFile can be created from TypedDict."""
        data: ImageFileTypedDict = {
            "file_name": "image.png",
            "content": b"\x89PNG\r\n\x1a\n",
            "content_type": "image/png",
        }
        file = ImageFile(**data)
        assert file.file_name == "image.png"


class TestImageEditRequestModel:
    """Tests for ImageEditRequest model."""

    def test_minimal_request(self) -> None:
        """Request with only required fields."""
        image = ImageFile(
            file_name="test.png",
            content=b"\x89PNG\r\n\x1a\n",
        )
        request = ImageEditRequest(
            image=image,
            prompt="Add a hat",
        )
        assert request.prompt == "Add a hat"
        assert request.n == 1  # default
        assert request.size == "1024x1024"  # default
        assert request.response_format == "url"  # default
        assert request.mask is None
        assert request.model is None
        assert request.user is None

    def test_full_request(self) -> None:
        """Request with all fields populated."""
        image = ImageFile(file_name="img.png", content=b"image_data")
        mask = ImageFile(file_name="mask.png", content=b"mask_data")

        request = ImageEditRequest(
            image=image,
            prompt="Replace background",
            model="dall-e-2",
            mask=mask,
            n=3,
            size="512x512",
            response_format="b64_json",
            user="user-123",
        )
        assert request.model == "dall-e-2"
        assert request.mask is not None
        assert request.n == 3
        assert request.size == "512x512"
        assert request.response_format == "b64_json"
        assert request.user == "user-123"

    def test_size_literal_values(self) -> None:
        """Size field only accepts valid literals."""
        image = ImageFile(file_name="t.png", content=b"x")

        for size in ["256x256", "512x512", "1024x1024"]:
            req = ImageEditRequest(image=image, prompt="test", size=size)
            assert req.size == size

    def test_response_format_literal_values(self) -> None:
        """response_format only accepts 'url' or 'b64_json'."""
        image = ImageFile(file_name="t.png", content=b"x")

        for fmt in ["url", "b64_json"]:
            req = ImageEditRequest(image=image, prompt="test", response_format=fmt)
            assert req.response_format == fmt
```

---

#### 2. SDK Method Tests (Mocked HTTP)

```python
class MockResponse:
    """Mock httpx.Response for testing."""

    def __init__(
        self,
        status_code: int = 200,
        json_data: Optional[dict] = None,
        text: str = "",
    ):
        self.status_code = status_code
        self._json_data = json_data or {}
        self.text = text
        self.headers = {"content-type": "application/json"}
        self.url = "https://api.example.com/images/edits"

    def json(self) -> dict:
        return self._json_data

    def read(self) -> bytes:
        return json.dumps(self._json_data).encode()


class TestImagesEdit:
    """Tests for images.edit() method."""

    @pytest.fixture
    def mock_response_success(self) -> dict:
        """Successful image edit response."""
        return {
            "created": 1699000000,
            "data": [
                {
                    "url": "https://example.com/edited-image.png",
                    "revised_prompt": "A person wearing a red hat",
                }
            ],
        }

    @pytest.fixture
    def png_bytes(self) -> bytes:
        """Minimal valid PNG bytes."""
        return b"\x89PNG\r\n\x1a\n" + b"\x00" * 100

    def test_edit_basic_request(
        self, mock_response_success: dict, png_bytes: bytes
    ) -> None:
        """Basic image edit request succeeds."""
        with patch.object(
            httpx.Client, "send", return_value=MockResponse(json_data=mock_response_success)
        ):
            with R9S(api_key="test-key") as client:
                result = client.images.edit(
                    image={"file_name": "test.png", "content": png_bytes},
                    prompt="Add a red hat",
                )

        assert result.created == 1699000000
        assert len(result.data) == 1
        assert result.data[0].url == "https://example.com/edited-image.png"

    def test_edit_with_mask(
        self, mock_response_success: dict, png_bytes: bytes
    ) -> None:
        """Image edit with mask file."""
        with patch.object(
            httpx.Client, "send", return_value=MockResponse(json_data=mock_response_success)
        ):
            with R9S(api_key="test-key") as client:
                result = client.images.edit(
                    image={"file_name": "photo.png", "content": png_bytes},
                    mask={"file_name": "mask.png", "content": png_bytes},
                    prompt="Replace background with beach",
                )

        assert result.data[0].url is not None

    def test_edit_with_all_params(
        self, mock_response_success: dict, png_bytes: bytes
    ) -> None:
        """Image edit with all optional parameters."""
        response = {
            "created": 1699000000,
            "data": [
                {"b64_json": base64.b64encode(png_bytes).decode()},
                {"b64_json": base64.b64encode(png_bytes).decode()},
            ],
        }

        with patch.object(
            httpx.Client, "send", return_value=MockResponse(json_data=response)
        ):
            with R9S(api_key="test-key") as client:
                result = client.images.edit(
                    image={"file_name": "img.png", "content": png_bytes},
                    prompt="Make it watercolor",
                    model="dall-e-2",
                    n=2,
                    size="512x512",
                    response_format="b64_json",
                    user="user-abc",
                )

        assert len(result.data) == 2
        assert result.data[0].b64_json is not None

    def test_edit_request_uses_multipart(self, png_bytes: bytes) -> None:
        """Verify request is sent as multipart/form-data."""
        captured_request = None

        def capture_request(request: httpx.Request) -> MockResponse:
            nonlocal captured_request
            captured_request = request
            return MockResponse(json_data={"created": 0, "data": []})

        with patch.object(httpx.Client, "send", side_effect=capture_request):
            with R9S(api_key="test-key") as client:
                client.images.edit(
                    image={"file_name": "test.png", "content": png_bytes},
                    prompt="Edit this",
                )

        assert captured_request is not None
        content_type = captured_request.headers.get("content-type", "")
        assert "multipart/form-data" in content_type

    def test_edit_request_path(self, png_bytes: bytes) -> None:
        """Verify request is sent to /images/edits endpoint."""
        captured_request = None

        def capture_request(request: httpx.Request) -> MockResponse:
            nonlocal captured_request
            captured_request = request
            return MockResponse(json_data={"created": 0, "data": []})

        with patch.object(httpx.Client, "send", side_effect=capture_request):
            with R9S(api_key="test-key", server_url="https://api.test.com") as client:
                client.images.edit(
                    image={"file_name": "test.png", "content": png_bytes},
                    prompt="Edit",
                )

        assert captured_request is not None
        assert "/images/edits" in str(captured_request.url)
```

---

#### 3. Async Method Tests

```python
class TestImagesEditAsync:
    """Tests for images.edit_async() method."""

    @pytest.fixture
    def png_bytes(self) -> bytes:
        return b"\x89PNG\r\n\x1a\n" + b"\x00" * 100

    @pytest.mark.asyncio
    async def test_edit_async_basic(self, png_bytes: bytes) -> None:
        """Async image edit request succeeds."""
        response_data = {
            "created": 1699000000,
            "data": [{"url": "https://example.com/result.png"}],
        }

        async def mock_send(*args, **kwargs):
            return MockResponse(json_data=response_data)

        with patch.object(httpx.AsyncClient, "send", side_effect=mock_send):
            async with R9S(api_key="test-key") as client:
                result = await client.images.edit_async(
                    image={"file_name": "test.png", "content": png_bytes},
                    prompt="Add sunglasses",
                )

        assert result.data[0].url == "https://example.com/result.png"

    @pytest.mark.asyncio
    async def test_edit_async_with_mask(self, png_bytes: bytes) -> None:
        """Async image edit with mask."""
        response_data = {"created": 0, "data": [{"url": "https://x.com/r.png"}]}

        async def mock_send(*args, **kwargs):
            return MockResponse(json_data=response_data)

        with patch.object(httpx.AsyncClient, "send", side_effect=mock_send):
            async with R9S(api_key="test-key") as client:
                result = await client.images.edit_async(
                    image={"file_name": "img.png", "content": png_bytes},
                    mask={"file_name": "mask.png", "content": png_bytes},
                    prompt="Remove background",
                )

        assert len(result.data) == 1
```

---

#### 4. Error Handling Tests

```python
class TestImagesEditErrors:
    """Tests for error handling in images.edit()."""

    @pytest.fixture
    def png_bytes(self) -> bytes:
        return b"\x89PNG\r\n\x1a\n" + b"\x00" * 100

    def test_bad_request_error(self, png_bytes: bytes) -> None:
        """400 Bad Request raises BadRequestError."""
        from r9s.errors import BadRequestError

        error_response = {
            "error": {
                "message": "Invalid image format",
                "type": "invalid_request_error",
                "code": "invalid_image",
            }
        }

        with patch.object(
            httpx.Client,
            "send",
            return_value=MockResponse(status_code=400, json_data=error_response),
        ):
            with R9S(api_key="test-key") as client:
                with pytest.raises(BadRequestError):
                    client.images.edit(
                        image={"file_name": "bad.jpg", "content": b"not-png"},
                        prompt="Edit",
                    )

    def test_authentication_error(self, png_bytes: bytes) -> None:
        """401 Unauthorized raises AuthenticationError."""
        from r9s.errors import AuthenticationError

        with patch.object(
            httpx.Client,
            "send",
            return_value=MockResponse(status_code=401, json_data={"error": {}}),
        ):
            with R9S(api_key="invalid-key") as client:
                with pytest.raises(AuthenticationError):
                    client.images.edit(
                        image={"file_name": "t.png", "content": png_bytes},
                        prompt="Edit",
                    )

    def test_rate_limit_error(self, png_bytes: bytes) -> None:
        """429 Too Many Requests raises RateLimitError."""
        from r9s.errors import RateLimitError

        with patch.object(
            httpx.Client,
            "send",
            return_value=MockResponse(status_code=429, json_data={"error": {}}),
        ):
            with R9S(api_key="test-key") as client:
                with pytest.raises(RateLimitError):
                    client.images.edit(
                        image={"file_name": "t.png", "content": png_bytes},
                        prompt="Edit",
                    )

    def test_unprocessable_entity_error(self, png_bytes: bytes) -> None:
        """422 raises UnprocessableEntityError for prompt issues."""
        from r9s.errors import UnprocessableEntityError

        with patch.object(
            httpx.Client,
            "send",
            return_value=MockResponse(status_code=422, json_data={"error": {}}),
        ):
            with R9S(api_key="test-key") as client:
                with pytest.raises(UnprocessableEntityError):
                    client.images.edit(
                        image={"file_name": "t.png", "content": png_bytes},
                        prompt="",  # Empty prompt
                    )

    def test_server_error(self, png_bytes: bytes) -> None:
        """500 Internal Server Error raises InternalServerError."""
        from r9s.errors import InternalServerError

        with patch.object(
            httpx.Client,
            "send",
            return_value=MockResponse(status_code=500, json_data={"error": {}}),
        ):
            with R9S(api_key="test-key") as client:
                with pytest.raises(InternalServerError):
                    client.images.edit(
                        image={"file_name": "t.png", "content": png_bytes},
                        prompt="Edit",
                    )

    def test_service_unavailable_error(self, png_bytes: bytes) -> None:
        """503 Service Unavailable raises ServiceUnavailableError."""
        from r9s.errors import ServiceUnavailableError

        with patch.object(
            httpx.Client,
            "send",
            return_value=MockResponse(status_code=503, json_data={"error": {}}),
        ):
            with R9S(api_key="test-key") as client:
                with pytest.raises(ServiceUnavailableError):
                    client.images.edit(
                        image={"file_name": "t.png", "content": png_bytes},
                        prompt="Edit",
                    )
```

---

#### 5. Retry Behavior Tests

```python
class TestImagesEditRetry:
    """Tests for retry behavior in images.edit()."""

    @pytest.fixture
    def png_bytes(self) -> bytes:
        return b"\x89PNG\r\n\x1a\n" + b"\x00" * 100

    def test_retries_on_429(self, png_bytes: bytes) -> None:
        """Request retries on 429 rate limit."""
        call_count = 0

        def mock_send(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                return MockResponse(status_code=429, json_data={"error": {}})
            return MockResponse(json_data={"created": 0, "data": []})

        with patch.object(httpx.Client, "send", side_effect=mock_send):
            with R9S(api_key="test-key") as client:
                # Should succeed after retries
                result = client.images.edit(
                    image={"file_name": "t.png", "content": png_bytes},
                    prompt="Edit",
                    retries={"strategy": "backoff", "max_retries": 3},
                )

        assert call_count == 3  # 2 failures + 1 success

    def test_retries_on_500(self, png_bytes: bytes) -> None:
        """Request retries on 500 server error."""
        call_count = 0

        def mock_send(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return MockResponse(status_code=500, json_data={"error": {}})
            return MockResponse(json_data={"created": 0, "data": []})

        with patch.object(httpx.Client, "send", side_effect=mock_send):
            with R9S(api_key="test-key") as client:
                result = client.images.edit(
                    image={"file_name": "t.png", "content": png_bytes},
                    prompt="Edit",
                    retries={"strategy": "backoff", "max_retries": 2},
                )

        assert call_count == 2
```

---

#### 6. Integration Test (Optional - requires API key)

```python
@pytest.mark.skipif(
    not os.environ.get("R9S_API_KEY"),
    reason="R9S_API_KEY not set"
)
class TestImagesEditIntegration:
    """Integration tests - require real API key."""

    @pytest.fixture
    def sample_png(self) -> bytes:
        """Create a minimal valid 1x1 PNG image."""
        # Minimal 1x1 white PNG
        return base64.b64decode(
            "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="
        )

    def test_edit_real_api(self, sample_png: bytes) -> None:
        """Test against real API (if key available)."""
        with R9S(api_key=os.environ["R9S_API_KEY"]) as client:
            result = client.images.edit(
                image={"file_name": "test.png", "content": sample_png},
                prompt="Add a small red dot",
                size="256x256",  # Smallest for speed
                n=1,
            )

        assert result.created > 0
        assert len(result.data) >= 1
        assert result.data[0].url or result.data[0].b64_json
```

---

#### Test File Structure

```
tests/
├── conftest.py                  # Existing fixtures
├── test_image_edit.py           # New file with all above tests
│   ├── TestImageFileModel
│   ├── TestImageEditRequestModel
│   ├── TestImagesEdit
│   ├── TestImagesEditAsync
│   ├── TestImagesEditErrors
│   ├── TestImagesEditRetry
│   └── TestImagesEditIntegration
└── ...
```

#### Running Tests

```bash
# Run all image edit tests
pytest tests/test_image_edit.py -v

# Run only model tests
pytest tests/test_image_edit.py::TestImageFileModel -v
pytest tests/test_image_edit.py::TestImageEditRequestModel -v

# Run only SDK method tests
pytest tests/test_image_edit.py::TestImagesEdit -v

# Run async tests
pytest tests/test_image_edit.py::TestImagesEditAsync -v

# Run error handling tests
pytest tests/test_image_edit.py::TestImagesEditErrors -v

# Run integration tests (requires API key)
R9S_API_KEY=your-key pytest tests/test_image_edit.py::TestImagesEditIntegration -v
```

---

### Reference: Existing Multipart Implementation

The SDK already implements multipart/form-data for audio transcription. Use `src/r9s/audio_sdk.py` and `src/r9s/models/audiotranscriptionrequest.py` as reference:

**Key patterns:**

1. File fields use `FieldMetadata(multipart=MultipartFormMetadata(file=True))`
2. Regular fields use `FieldMetadata(multipart=True)`
3. Serialization uses `utils.serialize_request_body(request, False, False, "multipart", ModelClass)`
4. File content uses `utils.get_pydantic_model(file, models.FileModel)` for conversion

---

## Future Considerations

### Not Supported by Gateway

1. **Image Variations** (`POST /v1/images/variations`) - Not implemented in gateway
2. **Batch Image Processing** - Not implemented

### Potential SDK Enhancements

1. **Progress Callbacks**: Stream generation progress for long-running requests
2. **Local Caching**: Cache generated images locally to reduce redundant API calls
3. **Helper Functions**: Convenience methods for common mask operations

### Gateway Enhancements (External)

1. **Image Variations Endpoint**: Support for creating variations of existing images
2. **More Provider Adaptors**: Support for emerging image generation providers
3. **Cost Optimization**: Automatic routing to cheapest provider for equivalent quality
