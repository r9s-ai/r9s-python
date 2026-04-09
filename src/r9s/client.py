from __future__ import annotations

import os
from typing import Optional

from r9s.parallel import CallResult, map_parallel, parallel
from r9s.sdk import R9S as _R9S


class R9S(_R9S):
    """Non-generated R9S helper with environment-based configuration."""

    @classmethod
    def from_env(
        cls,
        *,
        api_key_env: str = "R9S_API_KEY",
        base_url_env: str = "R9S_BASE_URL",
        default_base_url: Optional[str] = "https://api.r9s.ai/v1",
        **kwargs,
    ) -> "R9S":
        api_key = (os.getenv(api_key_env) or "").strip()
        if not api_key:
            raise ValueError(f"{api_key_env} is not set.")

        base_url = (os.getenv(base_url_env) or "").strip()
        if not base_url:
            base_url = (default_base_url or "").strip()

        if base_url:
            kwargs.setdefault("server_url", base_url)

        return cls(api_key=api_key, **kwargs)
