"""Tests for image generation functionality."""

from __future__ import annotations

from r9s.models.imagegenerationrequest import (
    ImageGenerationRequest,
    ImageGenerationRequestTypedDict,
)
from r9s.models.imagegenerationresponse import (
    ImageGenerationResponse,
    ImageUsage,
    ImageUsageTypedDict,
)
from r9s.models.imageobject import ImageObject


class TestImageGenerationRequestModel:
    """Tests for ImageGenerationRequest model."""

    def test_minimal_request(self) -> None:
        """Request with only required fields."""
        request = ImageGenerationRequest(prompt="A beautiful sunset")
        assert request.prompt == "A beautiful sunset"
        assert request.model is None
        assert request.n == 1
        assert request.quality == "standard"
        assert request.response_format == "url"
        assert request.size == "1024x1024"
        assert request.style == "vivid"
        assert request.user is None
        # Extended parameters default to None
        assert request.negative_prompt is None
        assert request.seed is None
        assert request.prompt_extend is None
        assert request.watermark is None

    def test_full_request_with_extended_params(self) -> None:
        """Request with all fields including extended parameters."""
        request = ImageGenerationRequest(
            prompt="A serene mountain landscape",
            model="wanx-v1",
            n=1,
            quality="hd",
            response_format="b64_json",
            size="1024x1024",
            style="natural",
            user="user-123",
            negative_prompt="people, buildings, cars",
            seed=12345,
            prompt_extend=True,
            watermark=False,
        )
        assert request.prompt == "A serene mountain landscape"
        assert request.model == "wanx-v1"
        assert request.quality == "hd"
        assert request.negative_prompt == "people, buildings, cars"
        assert request.seed == 12345
        assert request.prompt_extend is True
        assert request.watermark is False

    def test_negative_prompt_parameter(self) -> None:
        """negative_prompt parameter works correctly."""
        request = ImageGenerationRequest(
            prompt="A forest",
            negative_prompt="fog, mist, rain",
        )
        assert request.negative_prompt == "fog, mist, rain"

    def test_seed_parameter(self) -> None:
        """seed parameter works correctly."""
        request = ImageGenerationRequest(
            prompt="A blue dragon",
            seed=42,
        )
        assert request.seed == 42

    def test_seed_max_value(self) -> None:
        """seed parameter accepts max Qwen value."""
        request = ImageGenerationRequest(
            prompt="Test",
            seed=2147483647,
        )
        assert request.seed == 2147483647

    def test_prompt_extend_parameter(self) -> None:
        """prompt_extend parameter works correctly."""
        request = ImageGenerationRequest(
            prompt="A cat",
            prompt_extend=True,
        )
        assert request.prompt_extend is True

        request = ImageGenerationRequest(
            prompt="A cat",
            prompt_extend=False,
        )
        assert request.prompt_extend is False

    def test_watermark_parameter(self) -> None:
        """watermark parameter works correctly."""
        request = ImageGenerationRequest(
            prompt="A dog",
            watermark=True,
        )
        assert request.watermark is True

        request = ImageGenerationRequest(
            prompt="A dog",
            watermark=False,
        )
        assert request.watermark is False


class TestImageGenerationRequestSizes:
    """Tests for Size literal values."""

    def test_standard_sizes(self) -> None:
        """Standard OpenAI sizes are accepted."""
        standard_sizes = ["256x256", "512x512", "1024x1024"]
        for size in standard_sizes:
            req = ImageGenerationRequest(prompt="test", size=size)  # type: ignore
            assert req.size == size

    def test_dalle3_sizes(self) -> None:
        """DALL-E 3 sizes are accepted."""
        dalle3_sizes = ["1792x1024", "1024x1792"]
        for size in dalle3_sizes:
            req = ImageGenerationRequest(prompt="test", size=size)  # type: ignore
            assert req.size == size

    def test_gpt_image_sizes(self) -> None:
        """GPT-Image-1/1.5 sizes are accepted."""
        gpt_sizes = ["1024x1536", "1536x1024"]
        for size in gpt_sizes:
            req = ImageGenerationRequest(prompt="test", size=size)  # type: ignore
            assert req.size == size

    def test_wanx_sizes(self) -> None:
        """Wanx/Ali sizes are accepted."""
        wanx_sizes = ["720x1280", "1280x720", "512x1024", "1024x768", "576x1024", "1024x576"]
        for size in wanx_sizes:
            req = ImageGenerationRequest(prompt="test", size=size)  # type: ignore
            assert req.size == size

    def test_gemini_aspect_ratios(self) -> None:
        """Gemini Nano Banana aspect ratios are accepted."""
        aspect_ratios = ["1:1", "16:9", "9:16", "4:3", "3:4", "3:2", "2:3", "5:4", "4:5", "21:9"]
        for ratio in aspect_ratios:
            req = ImageGenerationRequest(prompt="test", size=ratio)  # type: ignore
            assert req.size == ratio


class TestImageGenerationRequestQuality:
    """Tests for Quality literal values."""

    def test_standard_quality_values(self) -> None:
        """Standard quality values are accepted."""
        for quality in ["standard", "hd"]:
            req = ImageGenerationRequest(prompt="test", quality=quality)  # type: ignore
            assert req.quality == quality

    def test_extended_quality_values(self) -> None:
        """Extended GPT-Image quality values are accepted."""
        for quality in ["low", "medium", "high"]:
            req = ImageGenerationRequest(prompt="test", quality=quality)  # type: ignore
            assert req.quality == quality


class TestImageGenerationRequestTypedDict:
    """Tests for ImageGenerationRequestTypedDict."""

    def test_typed_dict_minimal(self) -> None:
        """TypedDict with only required fields."""
        data: ImageGenerationRequestTypedDict = {
            "prompt": "A beautiful sunset",
        }
        assert data["prompt"] == "A beautiful sunset"

    def test_typed_dict_with_extended_params(self) -> None:
        """TypedDict with extended parameters."""
        data: ImageGenerationRequestTypedDict = {
            "prompt": "A mountain landscape",
            "model": "wanx-v1",
            "negative_prompt": "people, buildings",
            "seed": 12345,
            "prompt_extend": True,
            "watermark": False,
        }
        assert data["negative_prompt"] == "people, buildings"
        assert data["seed"] == 12345
        assert data["prompt_extend"] is True
        assert data["watermark"] is False


class TestImageUsageModel:
    """Tests for ImageUsage model."""

    def test_empty_usage(self) -> None:
        """ImageUsage with no fields set."""
        usage = ImageUsage()
        assert usage.prompt_tokens is None
        assert usage.image_tokens is None
        assert usage.input_text_tokens is None
        assert usage.output_image_tokens is None
        assert usage.width is None
        assert usage.height is None
        assert usage.image_count is None

    def test_openai_usage(self) -> None:
        """ImageUsage with OpenAI-style fields."""
        usage = ImageUsage(
            prompt_tokens=100,
            image_tokens=500,
        )
        assert usage.prompt_tokens == 100
        assert usage.image_tokens == 500

    def test_qwen_usage(self) -> None:
        """ImageUsage with Qwen-style fields."""
        usage = ImageUsage(
            input_text_tokens=50,
            output_image_tokens=1000,
            width=1024,
            height=1024,
            image_count=1,
        )
        assert usage.input_text_tokens == 50
        assert usage.output_image_tokens == 1000
        assert usage.width == 1024
        assert usage.height == 1024
        assert usage.image_count == 1

    def test_full_usage(self) -> None:
        """ImageUsage with all fields populated."""
        usage = ImageUsage(
            prompt_tokens=100,
            image_tokens=500,
            input_text_tokens=50,
            output_image_tokens=1000,
            width=1024,
            height=768,
            image_count=2,
        )
        assert usage.prompt_tokens == 100
        assert usage.image_tokens == 500
        assert usage.input_text_tokens == 50
        assert usage.output_image_tokens == 1000
        assert usage.width == 1024
        assert usage.height == 768
        assert usage.image_count == 2


class TestImageUsageTypedDict:
    """Tests for ImageUsageTypedDict."""

    def test_typed_dict_empty(self) -> None:
        """TypedDict with no fields."""
        data: ImageUsageTypedDict = {}
        assert len(data) == 0

    def test_typed_dict_full(self) -> None:
        """TypedDict with all fields."""
        data: ImageUsageTypedDict = {
            "prompt_tokens": 100,
            "image_tokens": 500,
            "input_text_tokens": 50,
            "output_image_tokens": 1000,
            "width": 1024,
            "height": 768,
            "image_count": 2,
        }
        assert data["prompt_tokens"] == 100
        assert data["image_tokens"] == 500


class TestImageGenerationResponseModel:
    """Tests for ImageGenerationResponse model."""

    def test_response_without_usage(self) -> None:
        """Response without usage information."""
        response = ImageGenerationResponse(
            created=1234567890,
            data=[ImageObject(url="https://example.com/image.png")],
        )
        assert response.created == 1234567890
        assert len(response.data) == 1
        assert response.data[0].url == "https://example.com/image.png"
        assert response.usage is None

    def test_response_with_usage(self) -> None:
        """Response with usage information."""
        usage = ImageUsage(prompt_tokens=100, image_tokens=500)
        response = ImageGenerationResponse(
            created=1234567890,
            data=[ImageObject(url="https://example.com/image.png")],
            usage=usage,
        )
        assert response.usage is not None
        assert response.usage.prompt_tokens == 100
        assert response.usage.image_tokens == 500

    def test_response_with_multiple_images(self) -> None:
        """Response with multiple images (gpt-image-1.5 style)."""
        response = ImageGenerationResponse(
            created=1234567890,
            data=[
                ImageObject(url="https://example.com/image1.png"),
                ImageObject(url="https://example.com/image2.png"),
                ImageObject(url="https://example.com/image3.png"),
            ],
        )
        assert len(response.data) == 3

    def test_response_with_b64_json(self) -> None:
        """Response with base64 encoded images."""
        response = ImageGenerationResponse(
            created=1234567890,
            data=[ImageObject(b64_json="iVBORw0KGgoAAAANSUhEUgAAAAEAAAAB...")],
        )
        assert response.data[0].b64_json is not None
        assert response.data[0].url is None

    def test_response_with_revised_prompt(self) -> None:
        """Response includes revised_prompt from DALL-E 3."""
        response = ImageGenerationResponse(
            created=1234567890,
            data=[
                ImageObject(
                    url="https://example.com/image.png",
                    revised_prompt="An enhanced description of the sunset",
                )
            ],
        )
        assert response.data[0].revised_prompt == "An enhanced description of the sunset"
