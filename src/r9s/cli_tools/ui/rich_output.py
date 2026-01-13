"""Lazy-loaded rich markdown rendering for chat output.

Rich is an optional dependency. If not installed, falls back to plain text.
Install with: pip install r9s[rich]
"""

from __future__ import annotations

import os
from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from rich.console import Console

# Lazy-loaded rich module
_rich_console: Optional["Console"] = None
_rich_available: Optional[bool] = None


def is_rich_enabled() -> bool:
    """Check if rich output is enabled via --rich flag or R9S_RICH env."""
    return os.getenv("R9S_RICH", "").lower() in ("1", "true", "yes")


def is_rich_available() -> bool:
    """Check if rich library is installed (lazy check)."""
    global _rich_available
    if _rich_available is None:
        try:
            import rich  # noqa: F401
            _rich_available = True
        except ImportError:
            _rich_available = False
    return _rich_available


def _get_console() -> "Console":
    """Get or create rich Console instance (lazy)."""
    global _rich_console
    if _rich_console is None:
        from rich.console import Console
        _rich_console = Console()
    return _rich_console


def print_markdown(text: str) -> None:
    """Print text as markdown using rich, or plain text if unavailable.

    Args:
        text: The markdown text to render
    """
    if not is_rich_available():
        print(text)
        return

    from rich.markdown import Markdown
    console = _get_console()
    md = Markdown(text)
    console.print(md)


def print_response(text: str, *, use_rich: bool = False) -> None:
    """Print assistant response, optionally with rich markdown rendering.

    Args:
        text: The response text
        use_rich: Whether to use rich markdown rendering
    """
    if use_rich and is_rich_available():
        print_markdown(text)
    else:
        print(text)


def format_tokens(input_tokens: int, output_tokens: int) -> str:
    """Format token usage for display.

    Args:
        input_tokens: Number of input/prompt tokens
        output_tokens: Number of output/completion tokens

    Returns:
        Formatted string like "tokens: 150 in / 89 out"
    """
    return f"tokens: {input_tokens} in / {output_tokens} out"
