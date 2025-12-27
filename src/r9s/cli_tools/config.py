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
    return (args_model or os.getenv("R9S_MODEL") or "").strip()


def resolve_system_prompt(
    args_system_prompt: Optional[str],
) -> Optional[str]:
    if args_system_prompt:
        val = args_system_prompt.strip()
        return val or None
    env = (os.getenv("R9S_SYSTEM_PROMPT") or "").strip()
    return env or None
