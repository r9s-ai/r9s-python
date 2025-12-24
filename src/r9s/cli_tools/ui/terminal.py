from getpass import getpass
import os
import sys
from typing import NewType

try:
    import termios
    import tty
except ImportError:  # e.g. Windows
    termios = None  # type: ignore[assignment]
    tty = None  # type: ignore[assignment]


ToolName = NewType("ToolName", str)

# Simple ANSI color helpers (no extra dependencies)
RESET = "\033[0m"
BOLD = "\033[1m"
FG_GREEN = "\033[32m"
FG_RED = "\033[31m"
FG_YELLOW = "\033[33m"
FG_CYAN = "\033[36m"


# True color (RGB) support
def rgb_color(r: int, g: int, b: int, bg: bool = False) -> str:
    """Generate ANSI escape code for 24-bit RGB color.

    Args:
        r: Red value (0-255)
        g: Green value (0-255)
        b: Blue value (0-255)
        bg: If True, set background color; otherwise set foreground

    Returns:
        ANSI escape code string
    """
    code = 48 if bg else 38
    return f"\033[{code};2;{r};{g};{b}m"


def hex_color(hex_code: str, bg: bool = False) -> str:
    """Convert hex color code to ANSI RGB escape sequence.

    Args:
        hex_code: Hex color like "#7c3aed" or "7c3aed"
        bg: If True, set background color; otherwise set foreground

    Returns:
        ANSI escape code string
    """
    hex_code = hex_code.lstrip("#")
    if len(hex_code) != 6:
        return ""
    try:
        r = int(hex_code[0:2], 16)
        g = int(hex_code[2:4], 16)
        b = int(hex_code[4:6], 16)
        return rgb_color(r, g, b, bg)
    except ValueError:
        return ""


# Brand colors
FG_PURPLE = hex_color("#7c3aed")  # Primary brand color
FG_PURPLE_LIGHT = hex_color("#a78bfa")  # Light purple for secondary text


def _style(text: str, *codes: str) -> str:
    return "".join(codes) + text + RESET


def info(message: str) -> None:
    print(_style(message, FG_CYAN))


def success(message: str) -> None:
    print(_style(message, FG_GREEN))


def warning(message: str) -> None:
    print(_style(message, FG_YELLOW))


def error(message: str) -> None:
    print(_style(message, FG_RED))


def header(message: str) -> None:
    print(_style(message, BOLD, FG_CYAN))


def prompt_text(message: str, *, color: str = FG_YELLOW) -> str:
    return input(_style(message, color)).strip()


def prompt_secret(message: str, *, color: str = FG_YELLOW) -> str:
    styled = _style(message, color)

    # If we don't have termios/tty support (e.g. on Windows), fall back to getpass.
    if termios is None or tty is None or os.name != "posix" or not sys.stdin.isatty():
        return getpass(styled).strip()

    sys.stdout.write(styled)
    sys.stdout.flush()

    fd = sys.stdin.fileno()
    old_settings = termios.tcgetattr(fd)
    chars: list[str] = []
    try:
        tty.setraw(fd)
        while True:
            ch = sys.stdin.read(1)
            # Enter / Return
            if ch in ("\r", "\n"):
                # Move to beginning of next line
                sys.stdout.write("\r\n")
                sys.stdout.flush()
                break
            # Ctrl+C
            if ch == "\x03":
                raise KeyboardInterrupt
            # Backspace / Delete
            if ch in ("\x7f", "\b"):
                if chars:
                    chars.pop()
                    sys.stdout.write("\b \b")
                    sys.stdout.flush()
                continue
            chars.append(ch)
            sys.stdout.write("*")
            sys.stdout.flush()
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)

    return "".join(chars).strip()


if __name__ == "__main__":
    header("r9s terminal style demo")
    info("This is an info message.")
    success("This is a success message.")
    warning("This is a warning message.")
    error("This is an error message.")
    name = prompt_text("Enter your name: ")
    secret = prompt_secret("Enter a secret (hidden): ")
    success(f"Hello, {name}! Your secret length is {len(secret)}.")
