# SDK Image Feature Update Requirements

This document outlines the required SDK updates based on a review of the AI Gateway (next-router) image capabilities across major providers.

## Executive Summary

The gateway supports image generation and editing across multiple providers with provider-specific parameters and constraints. The SDK needs updates to expose these capabilities while maintaining OpenAI API compatibility.

---

## 1. Gateway Provider Support Matrix

### Image Generation (`POST /v1/images/generations`)

| Provider | Status | Models | Key Constraints |
|----------|--------|--------|-----------------|
| **OpenAI** | Full | dall-e-2, dall-e-3, gpt-image-1, gpt-image-1.5 | Size/quality varies by model |
| **Gemini (Nano Banana)** | Full | gemini-2.5-flash-image, gemini-3-pro-image-preview | 10 aspect ratios, quality→resolution mapping |
| **Minimax** | Full | image-01 | Aspect ratio or custom WxH, prompt max 1500 chars |
| **Ali/Qwen** | Full | wanx-v1, ali-stable-diffusion-xl/v1.5 | Prompt max 800 chars, n=1 only |
| **Replicate** | Full | flux-schnell, flux-pro, etc. | Async polling, WebP->PNG conversion |
| **Zhipu** | Full | cogview-3 | n=1, prompt max 833 chars |

### Image Editing (`POST /v1/images/edits`)

| Provider | Status | Notes |
|----------|--------|-------|
| **OpenAI** | Full | dall-e-2 only, multipart/form-data |
| **Gemini** | Supported | Uses default validation |
| **Minimax** | Supported | Uses default validation |
| **Others** | Default | Pass-through with basic validation |

---

## 2. Provider-Specific Parameters (Not in Current SDK)

### 2.1 Extended ImageRequest Fields

The gateway `ImageRequest` struct supports these fields that the SDK does not currently expose:

```go
// Gateway: channel/channelmodel/image.go
type ImageRequest struct {
    // Standard OpenAI fields (already in SDK)
    Model          string
    Prompt         string
    N              int
    Size           string
    Quality        string
    ResponseFormat string
    Style          string
    User           string

    // Extended fields (NOT in SDK - need to add)
    NegativePrompt   string  // Qwen/Stability: exclude elements from generation
    PromptExtend     *bool   // Qwen: AI prompt optimization
    Watermark        *bool   // Qwen: add watermark to output
    Seed             *int64  // Reproducibility across providers
    Stream           bool    // Streaming support (provider-dependent)
    SafetyIdentifier string  // Content moderation tracking
}
```

### 2.2 SDK Model Update Required

Add to `src/r9s/models/imagegenerationrequest.py`:

```python
class ImageGenerationRequest(BaseModel):
    # ... existing fields ...

    # Extended parameters for advanced providers
    negative_prompt: Annotated[
        Optional[str],
        FieldMetadata(form=FormMetadata(style="form", explode=True))
    ] = None
    r"""Negative prompt to exclude elements (Qwen, Stability). Max 500 chars for Qwen."""

    seed: Annotated[
        Optional[int],
        FieldMetadata(form=FormMetadata(style="form", explode=True))
    ] = None
    r"""Random seed for reproducibility. Range: 0-2147483647 for Qwen."""

    prompt_extend: Annotated[
        Optional[bool],
        FieldMetadata(form=FormMetadata(style="form", explode=True))
    ] = None
    r"""Enable AI prompt optimization (Qwen-specific)."""

    watermark: Annotated[
        Optional[bool],
        FieldMetadata(form=FormMetadata(style="form", explode=True))
    ] = None
    r"""Add watermark to generated images (Qwen-specific)."""
```

---

## 3. Provider-Specific Constraints

### 3.1 OpenAI

**File Reference:** `channel/adaptor/openai/image_validation.go`

| Model | Sizes | N Range | Prompt Max | Notes |
|-------|-------|---------|------------|-------|
| dall-e-2 | 256x256, 512x512, 1024x1024 | 1-10 | 1000 chars | Legacy model |
| dall-e-3 | 1024x1024, 1024x1792, 1792x1024 | 1 | 4000 chars | High quality |
| gpt-image-1 | 1024x1024, 1024x1536, 1536x1024 | 1 | 4000 chars | |
| gpt-image-1.5 | 1024x1024, 1024x1536, 1536x1024 | 1-10 | 4000 chars | 4x faster, 20% cheaper than gpt-image-1 |

**Key Differences (gpt-image-1 vs gpt-image-1.5):**
- `gpt-image-1`: n=1 only
- `gpt-image-1.5`: n=1-10, 4x faster generation, 20% lower cost, better instruction following

**Cost Ratios:**
```python
OPENAI_SIZE_RATIOS = {
    "dall-e-2": {"256x256": 1.0, "512x512": 1.125, "1024x1024": 1.25},
    "dall-e-3": {"1024x1024": 1.0, "1024x1792": 2.0, "1792x1024": 2.0},
    "gpt-image-1": {"1024x1024": 1.0, "1024x1536": 2.0, "1536x1024": 2.0},
    "gpt-image-1.5": {"1024x1024": 1.0, "1024x1536": 2.0, "1536x1024": 2.0},
}
```

### 3.2 Gemini (Nano Banana)

**File Reference:** `channel/adaptor/gemini/adaptor.go`, `handler.go`, `model.go`

**Models:**
- `gemini-2.5-flash-image` - Nano Banana (standard)
- `gemini-2.5-flash-preview-05-20` - Preview version
- `gemini-3-pro-image-preview` - Nano Banana Pro (supports 4K)

**API Format (Updated):**
- **Endpoint:** `POST /v1beta/models/{model}:generateContent`
- **Request:** Uses `responseModalities: ["TEXT", "IMAGE"]` with `imageConfig`
- **Response Format:** Returns `b64_json` in `inlineData.data`

**Supported Aspect Ratios (10 total):**
```
1:1, 16:9, 9:16, 4:3, 3:4, 3:2, 2:3, 5:4, 4:5, 21:9
```

**Resolution Options:**
| Quality | ImageSize | Notes |
|---------|-----------|-------|
| standard | 1K | Default |
| hd | 2K | Higher quality |
| - | 4K | gemini-3-pro-image-preview only |

**Request Conversion (New):**
```go
// Gemini converts ImageRequest to ChatRequest with Nano Banana format
chatRequest := &ChatRequest{
    Contents: []ChatContent{{
        Parts: []Part{{Text: request.Prompt}},
    }},
    GenerationConfig: ChatGenerationConfig{
        ResponseModalities: []string{"TEXT", "IMAGE"},
        ImageConfig: &ImageConfig{
            AspectRatio: "1:1",   // from size or aspect_ratio param
            ImageSize:   "1K",    // "1K", "2K", or "4K"
        },
    },
}
```

**Size Mapping (OpenAI → Gemini):**
```python
GEMINI_ASPECT_RATIOS = {
    "1024x1024": "1:1",
    "1792x1024": "16:9",
    "1024x1792": "9:16",
    "1152x864":  "4:3",
    "864x1152":  "3:4",
    "1248x832":  "3:2",
    "832x1248":  "2:3",
    "1280x1024": "5:4",
    "1024x1280": "4:5",
    "1344x576":  "21:9",
}
```

**Constraints:**
| Constraint | Value |
|------------|-------|
| N range | 1 only |
| Prompt max | ~32,000 chars (token-based) |
| Response format | b64_json only |

**Pricing:**
- $0.039 per image (1,290 tokens @ $30/1M output tokens)
- Free tier: ~1,500 daily requests via Google AI Studio

### 3.3 Minimax

**File Reference:** `channel/adaptor/minimax/image.go`

| Constraint | Value |
|------------|-------|
| Prompt max | 1500 characters |
| N range | 1-9 |
| Width/Height | 512-2048, must be multiple of 8 |
| Response formats | `url`, `b64_json`, `base64` |

**Aspect Ratio Mapping:**
```python
MINIMAX_ASPECT_RATIOS = {
    "1:1":  (1024, 1024),
    "16:9": (1280, 720),
    "4:3":  (1152, 864),
    "3:2":  (1248, 832),
    "2:3":  (832, 1248),
    "3:4":  (864, 1152),
    "9:16": (720, 1280),
    "21:9": (1344, 576),
}
```

**Special Parameters:**
- `prompt_optimizer` -> `PromptOptimizer`
- `watermark` -> `AIGCWatermark`
- `seed` -> `Seed`

### 3.4 Ali/Qwen (Wanx)

**File Reference:** `channel/adaptor/ali/image_validation.go`, `image/` directory

| Constraint | Value |
|------------|-------|
| Prompt max | 800 characters |
| Negative prompt max | 500 characters |
| N | Fixed at 1 |
| Seed range | 0-2147483647 |

**Models:**
- `wanx-v1` - sizes: 1024x1024, 720x1280, 1280x720
- `ali-stable-diffusion-xl` - sizes: 512x1024, 1024x768, 1024x1024, 576x1024, 1024x576
- `ali-stable-diffusion-v1.5` - same sizes as xl

**Response Conversion:**
Gateway downloads Qwen image URLs and converts to OpenAI format, supporting both `url` and `b64_json` response formats.

### 3.5 Replicate

**File Reference:** `channel/adaptor/replicate/image.go`

**Async Processing Flow:**
1. Submit task -> receive task ID
2. Poll status every 3 seconds
3. Download generated images
4. Convert WebP/JPEG to PNG
5. Return as base64

**Image Format Handling:**
```go
// Automatically converts to PNG
func ConvertImageToPNG(data []byte) ([]byte, error) {
    // Handles: PNG (passthrough), JPEG (decode+encode), WebP (decode+encode)
}
```

### 3.6 Zhipu (CogView)

**File Reference:** Billing extractor at `relay/billing/extractor/zhipu_extractor.go`

| Model | N | Prompt Max |
|-------|---|------------|
| cogview-3 | 1 | 833 chars |

---

## 4. SDK Updates Required

### 4.1 New Model: Extended Image Request

Create/update `src/r9s/models/imagegenerationrequest.py`:

```python
# Add new type literals for extended sizes
ImageSize = Literal[
    "256x256", "512x512", "1024x1024",  # Standard
    "1024x1792", "1792x1024",            # DALL-E 3 landscape/portrait
    "1024x1536", "1536x1024",            # GPT-Image-1
    "720x1280", "1280x720",              # Wanx mobile
    "512x1024", "1024x768", "576x1024", "1024x576",  # Ali SD
]

# Add aspect ratio support for Minimax
AspectRatio = Literal["1:1", "16:9", "4:3", "3:2", "2:3", "3:4", "9:16", "21:9"]
```

### 4.2 New Method: `images.create()` with Extended Parameters

Update `src/r9s/images.py`:

```python
def create(
    self,
    *,
    prompt: str,
    model: Optional[str] = None,
    n: Optional[int] = 1,
    quality: Optional[Quality] = "standard",
    response_format: Optional[ResponseFormat] = "url",
    size: Optional[Size] = "1024x1024",
    style: Optional[Style] = "vivid",
    user: Optional[str] = None,
    # NEW: Extended parameters
    negative_prompt: Optional[str] = None,
    seed: Optional[int] = None,
    prompt_extend: Optional[bool] = None,
    watermark: Optional[bool] = None,
    # ... existing params
) -> models.ImageGenerationResponse:
    """Generate images with extended provider support."""
```

### 4.3 Update Response Model for Usage

Update `src/r9s/models/imagegenerationresponse.py`:

```python
class ImageUsage(BaseModel):
    """Usage information for image generation (provider-dependent)."""
    prompt_tokens: Optional[int] = None
    image_tokens: Optional[int] = None      # GPT-Image-1
    input_text_tokens: Optional[int] = None  # Qwen
    output_image_tokens: Optional[int] = None  # Qwen
    width: Optional[int] = None              # Qwen
    height: Optional[int] = None             # Qwen
    image_count: Optional[int] = None        # Qwen


class ImageGenerationResponse(BaseModel):
    created: int
    data: List[ImageObject]
    usage: Optional[ImageUsage] = None  # NEW: Optional usage info
```

### 4.4 Add Provider Constraint Helpers

Create `src/r9s/utils/image_constraints.py`:

```python
"""Provider-specific constraints for image generation."""

from dataclasses import dataclass
from typing import List, Tuple, Optional


@dataclass
class ModelConstraints:
    sizes: List[str]
    n_range: Tuple[int, int]
    prompt_max: int
    supports_negative_prompt: bool = False
    supports_seed: bool = False
    supports_aspect_ratio: bool = False  # Gemini, Minimax
    supports_4k: bool = False            # gemini-3-pro-image-preview only


MODEL_CONSTRAINTS = {
    "dall-e-2": ModelConstraints(
        sizes=["256x256", "512x512", "1024x1024"],
        n_range=(1, 10),
        prompt_max=1000,
    ),
    "dall-e-3": ModelConstraints(
        sizes=["1024x1024", "1024x1792", "1792x1024"],
        n_range=(1, 1),
        prompt_max=4000,
    ),
    "gpt-image-1": ModelConstraints(
        sizes=["1024x1024", "1024x1536", "1536x1024"],
        n_range=(1, 1),
        prompt_max=4000,
    ),
    "gpt-image-1.5": ModelConstraints(
        sizes=["1024x1024", "1024x1536", "1536x1024"],
        n_range=(1, 10),  # Supports multiple images unlike gpt-image-1
        prompt_max=4000,
    ),
    "wanx-v1": ModelConstraints(
        sizes=["1024x1024", "720x1280", "1280x720"],
        n_range=(1, 1),
        prompt_max=800,
        supports_negative_prompt=True,
        supports_seed=True,
    ),
    "cogview-3": ModelConstraints(
        sizes=[],  # No size validation
        n_range=(1, 1),
        prompt_max=833,
    ),
    # Gemini Nano Banana models - support aspect ratios
    "gemini-2.5-flash-image": ModelConstraints(
        sizes=["1:1", "16:9", "9:16", "4:3", "3:4", "3:2", "2:3", "5:4", "4:5", "21:9",
               "1024x1024", "1792x1024", "1024x1792"],
        n_range=(1, 1),
        prompt_max=32000,
        supports_aspect_ratio=True,
    ),
    "gemini-3-pro-image-preview": ModelConstraints(
        sizes=["1:1", "16:9", "9:16", "4:3", "3:4", "3:2", "2:3", "5:4", "4:5", "21:9",
               "1024x1024", "1792x1024", "1024x1792"],
        n_range=(1, 1),
        prompt_max=32000,
        supports_aspect_ratio=True,
        supports_4k=True,
    ),
}


def get_model_constraints(model: str) -> Optional[ModelConstraints]:
    """Get constraints for a specific model."""
    return MODEL_CONSTRAINTS.get(model)


def validate_image_request(
    model: str,
    prompt: str,
    size: Optional[str] = None,
    n: Optional[int] = None,
) -> List[str]:
    """Validate image request parameters. Returns list of error messages."""
    errors = []
    constraints = get_model_constraints(model)

    if not constraints:
        return errors  # Unknown model, skip validation

    if len(prompt) > constraints.prompt_max:
        errors.append(
            f"Prompt too long for {model}: {len(prompt)} > {constraints.prompt_max}"
        )

    if size and constraints.sizes and size not in constraints.sizes:
        errors.append(
            f"Invalid size for {model}: {size}. Valid: {constraints.sizes}"
        )

    if n is not None:
        min_n, max_n = constraints.n_range
        if n < min_n or n > max_n:
            errors.append(
                f"Invalid n for {model}: {n}. Range: {min_n}-{max_n}"
            )

    return errors
```

### 4.5 Documentation Updates

Update `docs/sdks/images/README.md`:

```markdown
## Extended Parameters

Some providers support additional parameters beyond the OpenAI standard:

### GPT-Image-1.5 (Multiple Images)

Generate multiple images in a single request with gpt-image-1.5:

```python
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
result = client.images.create(
    prompt="A serene mountain landscape",
    negative_prompt="people, buildings, cars",
    model="wanx-v1"
)
```

### Seed (Reproducibility)

Generate consistent results with the same seed:

```python
result = client.images.create(
    prompt="A blue dragon",
    seed=12345,
    model="wanx-v1"
)
```

### Gemini Nano Banana (Aspect Ratios)

Use aspect ratios for precise image dimensions:

```python
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
| Gemini Nano Banana | 32000 | 1 | aspect_ratio, quality→resolution |
| Gemini Nano Banana Pro | 32000 | 1 | aspect_ratio, 4K support |
| Qwen/Wanx | 800 | 1 | negative_prompt, seed |
| Minimax | 1500 | 1-9 | aspect_ratio |
| CogView | 833 | 1 | |
```

---

## 5. Testing Requirements

### 5.1 New Test Cases

Add to `tests/test_images.py`:

```python
class TestImageGenerationExtended:
    """Tests for extended image generation parameters."""

    def test_negative_prompt_qwen(self):
        """Negative prompt is included in Qwen requests."""
        ...

    def test_seed_parameter(self):
        """Seed parameter produces consistent results."""
        ...

    def test_prompt_length_validation(self):
        """Prompt length is validated per model."""
        ...

    def test_size_validation_per_model(self):
        """Size options are validated per model."""
        ...

    def test_n_range_validation(self):
        """N parameter is validated per model range."""
        ...
```

### 5.2 Integration Tests

```python
@pytest.mark.integration
class TestImageProviders:
    """Integration tests for each provider."""

    @pytest.mark.parametrize("model,size", [
        ("dall-e-2", "512x512"),
        ("dall-e-3", "1024x1024"),
        ("gpt-image-1", "1024x1024"),
        ("gpt-image-1.5", "1024x1024"),
        ("gpt-image-1.5", "1536x1024"),  # Test n>1 support
        ("wanx-v1", "1024x1024"),
        ("gemini-2.5-flash-image", "1:1"),
        ("gemini-2.5-flash-image", "16:9"),
        ("gemini-3-pro-image-preview", "1024x1024"),
    ])
    def test_generation_by_provider(self, model, size):
        """Generate image with each supported provider."""
        ...

    def test_gemini_aspect_ratio_mapping(self):
        """Verify OpenAI sizes map correctly to Gemini aspect ratios."""
        ...

    def test_gemini_quality_to_resolution(self):
        """Verify quality param maps to correct imageSize."""
        ...

    def test_gpt_image_15_multiple_images(self):
        """Verify gpt-image-1.5 supports generating multiple images (n=1-10)."""
        result = client.images.create(
            prompt="Test image",
            model="gpt-image-1.5",
            n=3,
            size="1024x1024"
        )
        assert len(result.data) == 3
```

---

## 6. Implementation Priority

### Phase 1: Core Updates (High Priority)
1. Add extended parameters to `ImageGenerationRequest`
2. Update `images.create()` signature
3. Add `ImageUsage` to response model

### Phase 2: Validation Helpers (Medium Priority)
4. Create `image_constraints.py` utility
5. Add client-side validation warnings

### Phase 3: Documentation & Tests (Medium Priority)
6. Update SDK documentation
7. Add comprehensive tests

### Phase 4: CLI Support (Lower Priority)
8. Expose extended params in CLI if applicable

---

## 7. Breaking Changes

None expected. All new parameters are optional with backward-compatible defaults.

---

## 8. Files to Modify

| File | Changes |
|------|---------|
| `src/r9s/models/imagegenerationrequest.py` | Add extended params |
| `src/r9s/models/imagegenerationresponse.py` | Add ImageUsage |
| `src/r9s/images.py` | Update create() signature |
| `src/r9s/models/__init__.py` | Export new types |
| `src/r9s/utils/image_constraints.py` | New file |
| `docs/sdks/images/README.md` | Document extended features |
| `tests/test_images.py` | Add new tests |

---

## Appendix: Gateway File References

| Gateway File | Purpose |
|--------------|---------|
| `channel/channelmodel/image.go` | Request/Response models |
| `channel/adaptor/openai/image_validation.go` | Size/prompt/n constraints |
| `channel/adaptor/gemini/adaptor.go` | Gemini image conversion |
| `channel/adaptor/minimax/image.go` | Minimax conversion & validation |
| `channel/adaptor/ali/image_validation.go` | Qwen validation |
| `channel/adaptor/ali/image/converter.go` | Qwen response conversion |
| `channel/adaptor/replicate/image.go` | Async polling & format conversion |
| `relay/controller/image.go` | Main request handlers |
