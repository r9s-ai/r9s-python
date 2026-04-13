from __future__ import annotations

import os
from typing import Optional

from r9s.user_config import get_user_config_string


def _resolve_value(args_value: Optional[str], env_key: str, config_key: str) -> Optional[str]:
    if args_value is not None:
        value = args_value.strip()
        return value or None
    env_value = (os.getenv(env_key) or "").strip()
    if env_value:
        return env_value
    return get_user_config_string(config_key)


def get_api_key(args_api_key: Optional[str]) -> Optional[str]:
    return _resolve_value(args_api_key, "R9S_API_KEY", "api_key")


def resolve_base_url(args_base_url: Optional[str]) -> str:
    return _resolve_value(args_base_url, "R9S_BASE_URL", "base_url") or "https://api.r9s.ai/v1"


def is_valid_url(url: str) -> bool:
    """Check if URL format is valid (must start with http:// or https://)."""
    if not url:
        return False
    url = url.strip()
    return url.startswith("http://") or url.startswith("https://")


def resolve_model(args_model: Optional[str]) -> str:
    return _resolve_value(args_model, "R9S_MODEL", "model") or "gpt-5-nano"


def resolve_image_model(args_model: Optional[str], default: str = "gpt-image-1.5") -> str:
    """Resolve image model: args > R9S_IMAGE_MODEL > default.

    Note: Does NOT fall back to R9S_MODEL since chat models are not valid for images.
    """
    return _resolve_value(args_model, "R9S_IMAGE_MODEL", "image_model") or default


def resolve_tts_model(args_model: Optional[str], default: str = "tts-1") -> str:
    """Resolve TTS model: args > R9S_TTS_MODEL > default."""
    return _resolve_value(args_model, "R9S_TTS_MODEL", "tts_model") or default


def resolve_stt_model(args_model: Optional[str], default: str = "whisper-1") -> str:
    """Resolve STT model: args > R9S_STT_MODEL > default."""
    return _resolve_value(args_model, "R9S_STT_MODEL", "stt_model") or default


def resolve_system_prompt(
    args_system_prompt: Optional[str],
) -> Optional[str]:
    return _resolve_value(args_system_prompt, "R9S_SYSTEM_PROMPT", "system_prompt")
