from __future__ import annotations

import argparse
import os
import shutil
import subprocess
from typing import List, Optional

from r9s.cli_tools.config import get_api_key, resolve_base_url, resolve_model
from r9s.cli_tools.tools.registry import APPS, supported_app_names_for_run
from r9s.cli_tools.ui.terminal import ToolName
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


def handle_run(args: argparse.Namespace) -> None:
    app = (args.app or "").strip().lower()
    tool = APPS.resolve(ToolName(app))
    if not tool:
        raise SystemExit(f"Unsupported app: {args.app}")
    if not tool.supports_run():
        supported = ", ".join(supported_app_names_for_run())
        raise SystemExit(
            f"Unsupported app for `r9s run`: {args.app} (supported: {supported})"
        )

    api_key = _require_api_key(getattr(args, "api_key", None))
    base_url = resolve_base_url(getattr(args, "base_url", None))
    model = _require_model(getattr(args, "model", None))

    exe = tool.run_executable()
    if not exe:
        raise SystemExit(f"Unsupported app for `r9s run`: {args.app}")
    exe_path = shutil.which(exe)
    if not exe_path:
        raise SystemExit(f"Command not found: {exe} (please install the app first)")

    cmd: List[str] = [exe_path, *list(getattr(args, "args", []) or [])]
    env = os.environ.copy()
    injected_env = tool.run_env(api_key=api_key, base_url=base_url, model=model)
    env.update(injected_env)

    if getattr(args, "print_env", False):
        for k in sorted(injected_env.keys()):
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
