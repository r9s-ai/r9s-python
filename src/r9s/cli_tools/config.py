from __future__ import annotations

import os
from typing import Optional


def get_api_key(args_api_key: Optional[str]) -> Optional[str]:
    value = (os.getenv("R9S_API_KEY") or args_api_key or "").strip()
    return value or None


def resolve_base_url(args_base_url: Optional[str]) -> str:
    return (
        args_base_url or os.getenv("R9S_BASE_URL") or "https://api.r9s.ai/v1"
    ).strip()


def is_valid_url(url: str) -> bool:
    """Check if URL format is valid (must start with http:// or https://)."""
    if not url:
        return False
    url = url.strip()
    return url.startswith("http://") or url.startswith("https://")


def resolve_model(args_model: Optional[str]) -> str:
    return (args_model or os.getenv("R9S_MODEL") or "gpt-5-nano").strip()


def resolve_image_model(args_model: Optional[str], default: str = "dall-e-3") -> str:
    """Resolve image model: args > R9S_IMAGE_MODEL > R9S_MODEL > default."""
    return (
        args_model
        or os.getenv("R9S_IMAGE_MODEL")
        or os.getenv("R9S_MODEL")
        or default
    ).strip()


def resolve_tts_model(args_model: Optional[str], default: str = "tts-1") -> str:
    """Resolve TTS model: args > R9S_TTS_MODEL > default."""
    return (args_model or os.getenv("R9S_TTS_MODEL") or default).strip()


def resolve_stt_model(args_model: Optional[str], default: str = "whisper-1") -> str:
    """Resolve STT model: args > R9S_STT_MODEL > default."""
    return (args_model or os.getenv("R9S_STT_MODEL") or default).strip()


def resolve_system_prompt(
    args_system_prompt: Optional[str],
) -> Optional[str]:
    if args_system_prompt:
        val = args_system_prompt.strip()
        return val or None
    env = (os.getenv("R9S_SYSTEM_PROMPT") or "").strip()
    return env or None
