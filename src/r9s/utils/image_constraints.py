"""Provider-specific constraints for image generation."""

from dataclasses import dataclass
from typing import List, Optional, Tuple


@dataclass
class ModelConstraints:
    """Constraints for a specific image generation model."""

    sizes: List[str]
    n_range: Tuple[int, int]
    prompt_max: int
    supports_negative_prompt: bool = False
    supports_seed: bool = False
    supports_aspect_ratio: bool = False
    supports_4k: bool = False


MODEL_CONSTRAINTS = {
    # OpenAI models
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
        n_range=(1, 10),
        prompt_max=4000,
    ),
    # Ali/Qwen models
    "wanx-v1": ModelConstraints(
        sizes=["1024x1024", "720x1280", "1280x720"],
        n_range=(1, 1),
        prompt_max=800,
        supports_negative_prompt=True,
        supports_seed=True,
    ),
    "ali-stable-diffusion-xl": ModelConstraints(
        sizes=["512x1024", "1024x768", "1024x1024", "576x1024", "1024x576"],
        n_range=(1, 1),
        prompt_max=800,
        supports_negative_prompt=True,
        supports_seed=True,
    ),
    "ali-stable-diffusion-v1.5": ModelConstraints(
        sizes=["512x1024", "1024x768", "1024x1024", "576x1024", "1024x576"],
        n_range=(1, 1),
        prompt_max=800,
        supports_negative_prompt=True,
        supports_seed=True,
    ),
    # Zhipu models
    "cogview-3": ModelConstraints(
        sizes=[],
        n_range=(1, 1),
        prompt_max=833,
    ),
    # Minimax models
    "image-01": ModelConstraints(
        sizes=["1:1", "16:9", "4:3", "3:2", "2:3", "3:4", "9:16", "21:9"],
        n_range=(1, 9),
        prompt_max=1500,
        supports_aspect_ratio=True,
        supports_seed=True,
    ),
    # Gemini Nano Banana models
    "gemini-2.5-flash-image": ModelConstraints(
        sizes=[
            "1:1",
            "16:9",
            "9:16",
            "4:3",
            "3:4",
            "3:2",
            "2:3",
            "5:4",
            "4:5",
            "21:9",
            "1024x1024",
            "1792x1024",
            "1024x1792",
        ],
        n_range=(1, 1),
        prompt_max=32000,
        supports_aspect_ratio=True,
    ),
    "gemini-2.5-flash-preview-05-20": ModelConstraints(
        sizes=[
            "1:1",
            "16:9",
            "9:16",
            "4:3",
            "3:4",
            "3:2",
            "2:3",
            "5:4",
            "4:5",
            "21:9",
            "1024x1024",
            "1792x1024",
            "1024x1792",
        ],
        n_range=(1, 1),
        prompt_max=32000,
        supports_aspect_ratio=True,
    ),
    "gemini-3-pro-image-preview": ModelConstraints(
        sizes=[
            "1:1",
            "16:9",
            "9:16",
            "4:3",
            "3:4",
            "3:2",
            "2:3",
            "5:4",
            "4:5",
            "21:9",
            "1024x1024",
            "1792x1024",
            "1024x1792",
        ],
        n_range=(1, 1),
        prompt_max=32000,
        supports_aspect_ratio=True,
        supports_4k=True,
    ),
}

# OpenAI size-based cost ratios
OPENAI_SIZE_RATIOS = {
    "dall-e-2": {"256x256": 1.0, "512x512": 1.125, "1024x1024": 1.25},
    "dall-e-3": {"1024x1024": 1.0, "1024x1792": 2.0, "1792x1024": 2.0},
    "gpt-image-1": {"1024x1024": 1.0, "1024x1536": 2.0, "1536x1024": 2.0},
    "gpt-image-1.5": {"1024x1024": 1.0, "1024x1536": 2.0, "1536x1024": 2.0},
}

# OpenAI size to Gemini aspect ratio mapping
GEMINI_ASPECT_RATIOS = {
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

# Minimax aspect ratio to pixel dimensions mapping
MINIMAX_ASPECT_RATIOS = {
    "1:1": (1024, 1024),
    "16:9": (1280, 720),
    "4:3": (1152, 864),
    "3:2": (1248, 832),
    "2:3": (832, 1248),
    "3:4": (864, 1152),
    "9:16": (720, 1280),
    "21:9": (1344, 576),
}


def get_model_constraints(model: str) -> Optional[ModelConstraints]:
    """Get constraints for a specific model.

    Args:
        model: The model name/identifier

    Returns:
        ModelConstraints if the model is known, None otherwise
    """
    return MODEL_CONSTRAINTS.get(model)


def validate_image_request(
    model: str,
    prompt: str,
    size: Optional[str] = None,
    n: Optional[int] = None,
    negative_prompt: Optional[str] = None,
) -> List[str]:
    """Validate image request parameters against model constraints.

    Args:
        model: The model name/identifier
        prompt: The image generation prompt
        size: Optional image size
        n: Optional number of images
        negative_prompt: Optional negative prompt

    Returns:
        List of error messages (empty if valid)
    """
    errors = []
    constraints = get_model_constraints(model)

    if not constraints:
        return errors  # Unknown model, skip validation

    if len(prompt) > constraints.prompt_max:
        errors.append(
            f"Prompt too long for {model}: {len(prompt)} > {constraints.prompt_max}"
        )

    if size and constraints.sizes and size not in constraints.sizes:
        errors.append(f"Invalid size for {model}: {size}. Valid: {constraints.sizes}")

    if n is not None:
        min_n, max_n = constraints.n_range
        if n < min_n or n > max_n:
            errors.append(f"Invalid n for {model}: {n}. Range: {min_n}-{max_n}")

    if negative_prompt is not None and not constraints.supports_negative_prompt:
        errors.append(f"Model {model} does not support negative_prompt")

    return errors


def get_gemini_aspect_ratio(size: str) -> Optional[str]:
    """Convert an OpenAI-style size to Gemini aspect ratio.

    Args:
        size: Size in "WxH" format or aspect ratio

    Returns:
        Aspect ratio string if mapping exists, None otherwise
    """
    # If it's already an aspect ratio, return as-is
    if ":" in size:
        return size
    return GEMINI_ASPECT_RATIOS.get(size)


def get_minimax_dimensions(aspect_ratio: str) -> Optional[Tuple[int, int]]:
    """Get Minimax pixel dimensions for an aspect ratio.

    Args:
        aspect_ratio: Aspect ratio in "W:H" format

    Returns:
        Tuple of (width, height) if mapping exists, None otherwise
    """
    return MINIMAX_ASPECT_RATIOS.get(aspect_ratio)
