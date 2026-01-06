"""Chat prompt with history and multi-line support using prompt_toolkit."""

from __future__ import annotations

from pathlib import Path
from typing import Optional

from prompt_toolkit import PromptSession
from prompt_toolkit.history import FileHistory
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.keys import Keys


def _get_history_path() -> Path:
    """Get the path for chat input history file."""
    path = Path.home() / ".r9s" / "input_history"
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


def create_chat_session(history_file: Optional[Path] = None) -> PromptSession:
    """Create a prompt session with history and multi-line support.

    Key bindings:
    - Enter: Submit input (single-line mode) or submit if on last line
    - Ctrl+J / Ctrl+Enter: Insert newline (for multi-line input)
    - Up/Down: Navigate history (when on first/last line)
    - Ctrl+A: Beginning of line
    - Ctrl+E: End of line
    - Ctrl+K: Kill to end of line
    - Ctrl+U: Kill to beginning of line
    - Ctrl+R: Reverse history search
    """
    history_path = history_file or _get_history_path()
    history = FileHistory(str(history_path))

    # Custom key bindings for multi-line support
    bindings = KeyBindings()

    @bindings.add(Keys.ControlJ)
    def _(event):
        """Ctrl+J inserts a newline."""
        event.current_buffer.insert_text("\n")

    session: PromptSession = PromptSession(
        history=history,
        multiline=False,  # Single-line by default, Ctrl+J to add lines
        key_bindings=bindings,
        enable_history_search=True,  # Ctrl+R for history search
    )
    return session


def chat_prompt(
    session: PromptSession,
    message: str = "",
    *,
    color: str = "\033[33m",  # Yellow by default
) -> str:
    """Prompt for chat input with history and editing support.

    Args:
        session: The PromptSession instance
        message: The prompt message to display
        color: ANSI color code for the prompt

    Returns:
        The user input text, stripped of leading/trailing whitespace

    Raises:
        EOFError: When user presses Ctrl+D
        KeyboardInterrupt: When user presses Ctrl+C
    """
    from prompt_toolkit.formatted_text import ANSI

    styled_message = f"{color}{message}\033[0m"
    result = session.prompt(ANSI(styled_message))
    return result.strip()
