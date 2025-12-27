from __future__ import annotations

import os
import re
import subprocess
import sys
from dataclasses import dataclass

from r9s.cli_tools.ui.terminal import FG_RED, prompt_text


@dataclass(frozen=True)
class RenderContext:
    args_text: str
    assume_yes: bool
    interactive: bool
    shell_timeout_seconds: int = 10
    shell_max_output_bytes: int = 1024 * 1024


_SHELL_RE = re.compile(r"!\{(.*?)\}", flags=re.DOTALL)


def _stderr(msg: str) -> None:
    print(msg, file=sys.stderr)


def _truncate_bytes(text: str, max_bytes: int) -> tuple[str, bool]:
    raw = text.encode("utf-8", errors="replace")
    if len(raw) <= max_bytes:
        return text, False
    truncated = raw[:max_bytes].decode("utf-8", errors="replace")
    return truncated, True


def render_template(template: str, ctx: RenderContext) -> str:
    rendered = template.replace("{{args}}", ctx.args_text)

    def repl(match: re.Match[str]) -> str:
        cmd = match.group(1).strip()
        if not cmd:
            return ""
        return _run_shell(cmd, ctx)

    if _SHELL_RE.search(rendered):
        rendered = _SHELL_RE.sub(repl, rendered)
    return rendered


def _confirm_shell(cmd: str) -> None:
    _stderr(f"[r9s] About to run: {cmd}")
    answer = prompt_text("Run this command? [y/N]: ", color=FG_RED).strip().lower()
    if answer not in ("y", "yes"):
        raise RuntimeError("Cancelled by user.")


def _run_shell(cmd: str, ctx: RenderContext) -> str:
    if not ctx.assume_yes:
        if not ctx.interactive:
            raise RuntimeError(
                "Shell execution requires confirmation. Pass -y to skip."
            )
        _confirm_shell(cmd)

    try:
        completed = subprocess.run(
            ["bash", "-lc", cmd],
            capture_output=True,
            text=True,
            timeout=ctx.shell_timeout_seconds,
            env=os.environ.copy(),
        )
    except subprocess.TimeoutExpired as exc:
        raise RuntimeError(
            f"Command timed out after {ctx.shell_timeout_seconds}s: {cmd}"
        ) from exc

    out = completed.stdout or ""
    err = completed.stderr or ""
    if completed.returncode != 0:
        err, _ = _truncate_bytes(err, 8 * 1024)
        raise RuntimeError(
            f"Command failed (exit {completed.returncode}): {cmd}\n{err}"
        )

    out, truncated = _truncate_bytes(out, ctx.shell_max_output_bytes)
    if truncated:
        _stderr(
            f"[r9s] Warning: command output exceeded {ctx.shell_max_output_bytes} bytes; truncated."
        )
    return out
