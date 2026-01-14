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
    file_max_bytes: int = 1024 * 1024


_SHELL_RE = re.compile(r"!\{(.*?)\}", flags=re.DOTALL)
_FILE_RE = re.compile(r"@\{(.*?)\}", flags=re.DOTALL)


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

    def repl_file(match: re.Match[str]) -> str:
        raw = match.group(1).strip()
        if not raw:
            return ""
        return _read_file(raw, ctx)

    if _FILE_RE.search(rendered):
        rendered = _FILE_RE.sub(repl_file, rendered)
    return rendered


def _resolve_file_max_bytes(ctx: RenderContext) -> int:
    raw = (os.getenv("R9S_FILE_INJECT_MAX_BYTES") or "").strip()
    if not raw:
        return ctx.file_max_bytes
    try:
        value = int(raw)
    except ValueError:
        return ctx.file_max_bytes
    return value if value > 0 else ctx.file_max_bytes


def _read_file(path_spec: str, ctx: RenderContext) -> str:
    from pathlib import Path

    path = Path(path_spec).expanduser()
    if not path.is_absolute():
        path = (Path.cwd() / path).resolve()

    try:
        data = path.read_bytes()
    except FileNotFoundError as exc:
        raise RuntimeError(f"File not found: {path}") from exc
    except OSError as exc:
        raise RuntimeError(f"Failed to read file: {path} ({exc})") from exc

    max_bytes = _resolve_file_max_bytes(ctx)
    if len(data) > max_bytes:
        raise RuntimeError(
            f"File too large to inject (max {max_bytes} bytes): {path} ({len(data)} bytes)"
        )
    if b"\x00" in data:
        raise RuntimeError(f"Binary file is not supported for injection: {path}")

    _stderr(f"[r9s] Injecting file: {path} ({len(data)} bytes)")
    try:
        return data.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise RuntimeError(f"File is not valid UTF-8: {path}") from exc


def _confirm_shell(cmd: str) -> None:
    _stderr(f"[r9s] About to run: {cmd}")
    answer = prompt_text("Run this command? [y/N]: ", color=FG_RED).strip().lower()
    if answer not in ("y", "yes"):
        raise SystemExit("Cancelled.")


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
