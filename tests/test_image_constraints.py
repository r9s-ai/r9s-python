"""Tests for image constraints utility module."""

from __future__ import annotations

import pytest

from r9s.utils.image_constraints import (
    MODEL_CONSTRAINTS,
    GEMINI_ASPECT_RATIOS,
    MINIMAX_ASPECT_RATIOS,
    OPENAI_SIZE_RATIOS,
    ModelConstraints,
    get_gemini_aspect_ratio,
    get_minimax_dimensions,
    get_model_constraints,
    validate_image_request,
)


class TestModelConstraints:
    """Tests for ModelConstraints dataclass."""

    def test_model_constraints_creation(self) -> None:
        """ModelConstraints can be created with all fields."""
        constraints = ModelConstraints(
            sizes=["1024x1024", "512x512"],
            n_range=(1, 10),
            prompt_max=1000,
            supports_negative_prompt=True,
            supports_seed=True,
            supports_aspect_ratio=False,
            supports_4k=False,
        )
        assert constraints.sizes == ["1024x1024", "512x512"]
        assert constraints.n_range == (1, 10)
        assert constraints.prompt_max == 1000
        assert constraints.supports_negative_prompt is True
        assert constraints.supports_seed is True
        assert constraints.supports_aspect_ratio is False
        assert constraints.supports_4k is False

    def test_model_constraints_defaults(self) -> None:
        """ModelConstraints has correct default values."""
        constraints = ModelConstraints(
            sizes=["1024x1024"],
            n_range=(1, 1),
            prompt_max=1000,
        )
        assert constraints.supports_negative_prompt is False
        assert constraints.supports_seed is False
        assert constraints.supports_aspect_ratio is False
        assert constraints.supports_4k is False


class TestGetModelConstraints:
    """Tests for get_model_constraints function."""

    def test_get_dalle2_constraints(self) -> None:
        """Get constraints for DALL-E 2."""
        constraints = get_model_constraints("dall-e-2")
        assert constraints is not None
        assert "256x256" in constraints.sizes
        assert "512x512" in constraints.sizes
        assert "1024x1024" in constraints.sizes
        assert constraints.n_range == (1, 10)
        assert constraints.prompt_max == 1000

    def test_get_dalle3_constraints(self) -> None:
        """Get constraints for DALL-E 3."""
        constraints = get_model_constraints("dall-e-3")
        assert constraints is not None
        assert "1024x1024" in constraints.sizes
        assert "1024x1792" in constraints.sizes
        assert "1792x1024" in constraints.sizes
        assert constraints.n_range == (1, 1)
        assert constraints.prompt_max == 4000

    def test_get_gpt_image_1_constraints(self) -> None:
        """Get constraints for gpt-image-1."""
        constraints = get_model_constraints("gpt-image-1")
        assert constraints is not None
        assert constraints.n_range == (1, 1)
        assert constraints.prompt_max == 4000

    def test_get_gpt_image_15_constraints(self) -> None:
        """Get constraints for gpt-image-1.5."""
        constraints = get_model_constraints("gpt-image-1.5")
        assert constraints is not None
        assert constraints.n_range == (1, 10)  # Supports multiple images
        assert constraints.prompt_max == 4000

    def test_get_wanx_constraints(self) -> None:
        """Get constraints for wanx-v1."""
        constraints = get_model_constraints("wanx-v1")
        assert constraints is not None
        assert constraints.prompt_max == 800
        assert constraints.supports_negative_prompt is True
        assert constraints.supports_seed is True

    def test_get_gemini_constraints(self) -> None:
        """Get constraints for Gemini Nano Banana."""
        constraints = get_model_constraints("gemini-2.5-flash-image")
        assert constraints is not None
        assert constraints.prompt_max == 32000
        assert constraints.supports_aspect_ratio is True
        assert "1:1" in constraints.sizes
        assert "16:9" in constraints.sizes

    def test_get_gemini_pro_constraints(self) -> None:
        """Get constraints for Gemini Nano Banana Pro with 4K support."""
        constraints = get_model_constraints("gemini-3-pro-image-preview")
        assert constraints is not None
        assert constraints.supports_4k is True
        assert constraints.supports_aspect_ratio is True

    def test_get_cogview_constraints(self) -> None:
        """Get constraints for CogView."""
        constraints = get_model_constraints("cogview-3")
        assert constraints is not None
        assert constraints.prompt_max == 833
        assert constraints.n_range == (1, 1)

    def test_get_minimax_constraints(self) -> None:
        """Get constraints for Minimax image-01."""
        constraints = get_model_constraints("image-01")
        assert constraints is not None
        assert constraints.n_range == (1, 9)
        assert constraints.prompt_max == 1500
        assert constraints.supports_aspect_ratio is True
        assert constraints.supports_seed is True

    def test_get_unknown_model_returns_none(self) -> None:
        """Unknown model returns None."""
        constraints = get_model_constraints("unknown-model")
        assert constraints is None


class TestValidateImageRequest:
    """Tests for validate_image_request function."""

    def test_valid_request(self) -> None:
        """Valid request returns no errors."""
        errors = validate_image_request(
            model="dall-e-2",
            prompt="A beautiful sunset",
            size="1024x1024",
            n=1,
        )
        assert errors == []

    def test_prompt_too_long(self) -> None:
        """Prompt exceeding max length returns error."""
        long_prompt = "x" * 1001  # DALL-E 2 max is 1000
        errors = validate_image_request(
            model="dall-e-2",
            prompt=long_prompt,
        )
        assert len(errors) == 1
        assert "Prompt too long" in errors[0]
        assert "1001 > 1000" in errors[0]

    def test_invalid_size(self) -> None:
        """Invalid size returns error."""
        errors = validate_image_request(
            model="dall-e-2",
            prompt="Test",
            size="2048x2048",  # Not valid for DALL-E 2
        )
        assert len(errors) == 1
        assert "Invalid size" in errors[0]

    def test_invalid_n_below_range(self) -> None:
        """n below valid range returns error."""
        errors = validate_image_request(
            model="dall-e-2",
            prompt="Test",
            n=0,
        )
        assert len(errors) == 1
        assert "Invalid n" in errors[0]

    def test_invalid_n_above_range(self) -> None:
        """n above valid range returns error."""
        errors = validate_image_request(
            model="dall-e-3",
            prompt="Test",
            n=5,  # DALL-E 3 only supports n=1
        )
        assert len(errors) == 1
        assert "Invalid n" in errors[0]
        assert "Range: 1-1" in errors[0]

    def test_gpt_image_15_supports_multiple_n(self) -> None:
        """gpt-image-1.5 supports n up to 10."""
        errors = validate_image_request(
            model="gpt-image-1.5",
            prompt="Test",
            n=5,
        )
        assert errors == []

        errors = validate_image_request(
            model="gpt-image-1.5",
            prompt="Test",
            n=11,  # Above max
        )
        assert len(errors) == 1
        assert "Invalid n" in errors[0]

    def test_negative_prompt_unsupported(self) -> None:
        """negative_prompt on unsupported model returns error."""
        errors = validate_image_request(
            model="dall-e-3",
            prompt="Test",
            negative_prompt="blur, noise",
        )
        assert len(errors) == 1
        assert "does not support negative_prompt" in errors[0]

    def test_negative_prompt_supported(self) -> None:
        """negative_prompt on supported model returns no error."""
        errors = validate_image_request(
            model="wanx-v1",
            prompt="Test",
            negative_prompt="blur, noise",
        )
        assert errors == []

    def test_unknown_model_skips_validation(self) -> None:
        """Unknown model skips validation."""
        errors = validate_image_request(
            model="unknown-model",
            prompt="x" * 10000,  # Very long prompt
            size="9999x9999",
            n=100,
        )
        assert errors == []

    def test_multiple_errors(self) -> None:
        """Multiple validation errors are all returned."""
        errors = validate_image_request(
            model="dall-e-2",
            prompt="x" * 1001,  # Too long
            size="2048x2048",  # Invalid
            n=20,  # Above max
        )
        assert len(errors) == 3

    def test_gemini_aspect_ratio_valid(self) -> None:
        """Gemini accepts aspect ratio as size."""
        errors = validate_image_request(
            model="gemini-2.5-flash-image",
            prompt="Test",
            size="16:9",
        )
        assert errors == []

    def test_qwen_prompt_max(self) -> None:
        """Qwen has 800 character limit."""
        errors = validate_image_request(
            model="wanx-v1",
            prompt="x" * 801,
        )
        assert len(errors) == 1
        assert "801 > 800" in errors[0]


class TestGeminiAspectRatioMapping:
    """Tests for Gemini aspect ratio mapping."""

    def test_get_gemini_aspect_ratio_from_size(self) -> None:
        """Get aspect ratio from OpenAI-style size."""
        assert get_gemini_aspect_ratio("1024x1024") == "1:1"
        assert get_gemini_aspect_ratio("1792x1024") == "16:9"
        assert get_gemini_aspect_ratio("1024x1792") == "9:16"

    def test_get_gemini_aspect_ratio_passthrough(self) -> None:
        """Aspect ratio strings pass through unchanged."""
        assert get_gemini_aspect_ratio("1:1") == "1:1"
        assert get_gemini_aspect_ratio("16:9") == "16:9"
        assert get_gemini_aspect_ratio("21:9") == "21:9"

    def test_get_gemini_aspect_ratio_unknown(self) -> None:
        """Unknown size returns None."""
        assert get_gemini_aspect_ratio("9999x9999") is None

    def test_gemini_aspect_ratios_mapping_complete(self) -> None:
        """All expected mappings exist."""
        expected = {
            "1024x1024": "1:1",
            "1792x1024": "16:9",
            "1024x1792": "9:16",
            "1152x864": "4:3",
            "864x1152": "3:4",
            "1248x832": "3:2",
            "832x1248": "2:3",
            "1280x1024": "5:4",
            "1024x1280": "4:5",
            "1344x576": "21:9",
        }
        for size, ratio in expected.items():
            assert GEMINI_ASPECT_RATIOS.get(size) == ratio


class TestMinimaxDimensionsMapping:
    """Tests for Minimax dimensions mapping."""

    def test_get_minimax_dimensions(self) -> None:
        """Get pixel dimensions from aspect ratio."""
        assert get_minimax_dimensions("1:1") == (1024, 1024)
        assert get_minimax_dimensions("16:9") == (1280, 720)
        assert get_minimax_dimensions("9:16") == (720, 1280)

    def test_get_minimax_dimensions_unknown(self) -> None:
        """Unknown aspect ratio returns None."""
        assert get_minimax_dimensions("99:1") is None

    def test_minimax_aspect_ratios_mapping_complete(self) -> None:
        """All expected mappings exist."""
        expected = {
            "1:1": (1024, 1024),
            "16:9": (1280, 720),
            "4:3": (1152, 864),
            "3:2": (1248, 832),
            "2:3": (832, 1248),
            "3:4": (864, 1152),
            "9:16": (720, 1280),
            "21:9": (1344, 576),
        }
        for ratio, dims in expected.items():
            assert MINIMAX_ASPECT_RATIOS.get(ratio) == dims


class TestOpenAISizeRatios:
    """Tests for OpenAI size cost ratios."""

    def test_dalle2_ratios(self) -> None:
        """DALL-E 2 size ratios are correct."""
        assert OPENAI_SIZE_RATIOS["dall-e-2"]["256x256"] == 1.0
        assert OPENAI_SIZE_RATIOS["dall-e-2"]["512x512"] == 1.125
        assert OPENAI_SIZE_RATIOS["dall-e-2"]["1024x1024"] == 1.25

    def test_dalle3_ratios(self) -> None:
        """DALL-E 3 size ratios are correct."""
        assert OPENAI_SIZE_RATIOS["dall-e-3"]["1024x1024"] == 1.0
        assert OPENAI_SIZE_RATIOS["dall-e-3"]["1024x1792"] == 2.0
        assert OPENAI_SIZE_RATIOS["dall-e-3"]["1792x1024"] == 2.0

    def test_gpt_image_ratios(self) -> None:
        """GPT-Image size ratios are correct."""
        for model in ["gpt-image-1", "gpt-image-1.5"]:
            assert OPENAI_SIZE_RATIOS[model]["1024x1024"] == 1.0
            assert OPENAI_SIZE_RATIOS[model]["1024x1536"] == 2.0
            assert OPENAI_SIZE_RATIOS[model]["1536x1024"] == 2.0


class TestModelConstraintsDict:
    """Tests for MODEL_CONSTRAINTS dictionary."""

    def test_all_openai_models_present(self) -> None:
        """All OpenAI models are in constraints dict."""
        openai_models = ["dall-e-2", "dall-e-3", "gpt-image-1", "gpt-image-1.5"]
        for model in openai_models:
            assert model in MODEL_CONSTRAINTS

    def test_all_gemini_models_present(self) -> None:
        """All Gemini models are in constraints dict."""
        gemini_models = [
            "gemini-2.5-flash-image",
            "gemini-2.5-flash-preview-05-20",
            "gemini-3-pro-image-preview",
        ]
        for model in gemini_models:
            assert model in MODEL_CONSTRAINTS

    def test_all_ali_models_present(self) -> None:
        """All Ali/Qwen models are in constraints dict."""
        ali_models = ["wanx-v1", "ali-stable-diffusion-xl", "ali-stable-diffusion-v1.5"]
        for model in ali_models:
            assert model in MODEL_CONSTRAINTS

    def test_other_models_present(self) -> None:
        """Other provider models are in constraints dict."""
        other_models = ["cogview-3", "image-01"]
        for model in other_models:
            assert model in MODEL_CONSTRAINTS
