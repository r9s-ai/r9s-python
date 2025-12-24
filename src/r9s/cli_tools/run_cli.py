from __future__ import annotations

import argparse
import os
import shutil
import subprocess
from typing import Dict, List, Optional

from r9s.cli_tools.config import get_api_key, resolve_base_url, resolve_model
from r9s.cli_tools.ui.terminal import FG_RED, error, info, prompt_text


def _require_model(args_model: Optional[str]) -> str:
    model = resolve_model(args_model)
    if not model:
        raise SystemExit("Missing model: pass --model or set R9S_MODEL")
    return model


def _require_api_key(args_api_key: Optional[str]) -> str:
    api_key = get_api_key(args_api_key)
    if not api_key:
        raise SystemExit("Missing API key: set R9S_API_KEY or pass --api-key")
    return api_key


def _anthropic_env(api_key: str, base_url: str, model: str) -> Dict[str, str]:
    return {
        "ANTHROPIC_AUTH_TOKEN": api_key,
        "ANTHROPIC_BASE_URL": base_url,
        "ANTHROPIC_MODEL": model,
        "ANTHROPIC_SMALL_FAST_MODEL": model,
        "ANTHROPIC_DEFAULT_SONNET_MODEL": model,
        "ANTHROPIC_DEFAULT_OPUS_MODEL": model,
        "ANTHROPIC_DEFAULT_HAIKU_MODEL": model,
    }


def handle_run(args: argparse.Namespace) -> None:
    app = (args.app or "").strip().lower()
    if app in ("claude-code", "claude_code", "claude"):
        app = "claude-code"
    if app == "cc":
        app = "claude-code"

    if app != "claude-code":
        raise SystemExit(f"Unsupported app: {args.app}")

    api_key = _require_api_key(getattr(args, "api_key", None))
    base_url = resolve_base_url(getattr(args, "base_url", None))
    model = _require_model(getattr(args, "model", None))

    claude = shutil.which("claude")
    if not claude:
        raise SystemExit("Command not found: claude (please install Claude Code CLI)")

    cmd: List[str] = [claude, *list(getattr(args, "args", []) or [])]
    env = os.environ.copy()
    env.update(_anthropic_env(api_key=api_key, base_url=base_url, model=model))

    if getattr(args, "print_env", False):
        for k in sorted(
            _anthropic_env(api_key=api_key, base_url=base_url, model=model).keys()
        ):
            print(f"{k}={env[k]}")
        return

    if getattr(args, "confirm", False):
        info("About to run:")
        print("  " + " ".join(cmd))
        answer = prompt_text("Proceed? [y/N]: ", color=FG_RED).lower()
        if answer not in ("y", "yes"):
            error("Cancelled.")
            return

    raise SystemExit(subprocess.call(cmd, env=env))
