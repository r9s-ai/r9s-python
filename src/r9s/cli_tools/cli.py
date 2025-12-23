import argparse
import json
import os
import shutil
import sys
import urllib.error
import urllib.request
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Tuple

from r9s.terminal import (
    FG_RED,
    FG_CYAN,
    ToolName,
    _style,
    error,
    header,
    info,
    prompt_secret,
    prompt_text,
    success,
    warning,
)
from r9s.tools.base import ToolConfigSetResult, ToolIntegration
from r9s.tools.claude_code import ClaudeCodeIntegration


class ToolRegistry:
    def __init__(self) -> None:
        self._registry: Dict[ToolName, ToolIntegration] = {}

    def register(self, name: ToolName, tool: ToolIntegration) -> None:
        self._registry[name] = tool
    def get(self, name: ToolName) -> Optional[ToolIntegration]:
        return self._registry.get(name)

    def primary_names(self) -> List[ToolName]:
        return sorted({tool.primary_name for tool in self._registry.values()})

    def resolve(self, name: ToolName) -> Optional[ToolIntegration]:
        if name in self._registry:
            return self._registry[name]
        normalized = name.lower().replace("_", "-")
        return self._registry.get(normalized)


TOOLS = ToolRegistry()
_claude_code = ClaudeCodeIntegration()
for alias in _claude_code.aliases:
    TOOLS.register(alias, _claude_code)


def masked_key(key: str, visible: int = 4) -> str:
    if len(key) <= visible:
        return "*" * len(key)
    return f"{key[:visible]}***{key[-visible:]}"


def prompt_choice(prompt: str, options: List[str]) -> str:
    for idx, value in enumerate(options, start=1):
        print(_style(f"{idx})", FG_CYAN), value)
    while True:
        selection = prompt_text(f"{prompt} (enter number): ")
        if not selection.isdigit():
            error("Please enter a valid number.")
            continue
        num = int(selection)
        if 1 <= num <= len(options):
            return options[num - 1]
        error("Selection out of range, try again.")


def prompt_yes_no(prompt: str, default_no: bool = True) -> bool:
    suffix = "[y/N]" if default_no else "[Y/n]"
    answer = prompt_text(f"{prompt} {suffix}: ").lower()
    if not answer:
        return not default_no
    return answer in ("y", "yes")


def fetch_models(base_url: str, api_key: str, timeout: int = 5) -> List[str]:
    url = base_url.rstrip("/") + "/v1/models"
    headers = {"Authorization": f"Bearer {api_key}"}
    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            payload = resp.read()
    except (urllib.error.URLError, TimeoutError) as exc:
        error(
            f"Failed to fetch model list from {url} ({exc}). "
            "You can enter a model manually."
        )
        return []

    try:
        data = json.loads(payload.decode("utf-8"))
    except json.JSONDecodeError:
        error("Model list response is not valid JSON. Skipping automatic selection.")
        return []

    if isinstance(data, list) and all(isinstance(item, str) for item in data):
        return data
    if isinstance(data, dict) and "data" in data and isinstance(data["data"], list):
        models = []
        for item in data["data"]:
            if isinstance(item, dict) and "id" in item:
                models.append(str(item["id"]))
            elif isinstance(item, str):
                models.append(item)
        return models
    error("Could not parse model list from response. Please enter a model manually.")
    return []


def choose_model(base_url: str, api_key: str, preset: Optional[str]) -> str:
    if preset:
        return preset
    models = fetch_models(base_url, api_key)
    if models:
        choice = prompt_choice("Select model", models)
        return choice
    manual = prompt_text("Enter model name: ")
    while not manual:
        manual = prompt_text("Model name cannot be empty. Enter model name: ", color=FG_RED)
    return manual


def resolve_base_url(args_base_url: Optional[str]) -> str:
    env_base = os.getenv("r9s_BASE_URL")
    if args_base_url:
        return args_base_url
    if env_base:
        return env_base
    return "https://api.r9s.ai"


def resolve_api_key(preset: Optional[str]) -> str:
    env_key = os.getenv("r9s_API_KEY")
    if env_key:
        return env_key
    if preset:
        return preset
    key = prompt_secret("r9s_API_KEY is not set. Enter API key: ")
    while not key:
        key = prompt_secret("API key cannot be empty. Enter API key: ", color=FG_RED)
    return key


def select_tool_name(arg_name: Optional[str]) -> Tuple[ToolIntegration, str]:
    if arg_name:
        tool = TOOLS.resolve(arg_name)
        if tool:
            return tool, tool.primary_name
        raise SystemExit(f"Unsupported tool: {arg_name}")
    available = TOOLS.primary_names()
    chosen = prompt_choice("Select tool to configure", available)
    tool = TOOLS.resolve(chosen)
    if not tool:
        raise SystemExit(f"Unsupported tool: {chosen}")
    return tool, tool.primary_name


def handle_set(args: argparse.Namespace) -> None:
    tool, tool_name = select_tool_name(args.tool)
    api_key = resolve_api_key(args.api_key)
    base_url = resolve_base_url(args.base_url)
    model = choose_model(base_url, api_key, args.model)

    header("\nConfiguration summary:")
    print(f"- Tool: {tool_name}")
    print(f"- Base URL: {base_url}")
    print(f"- Model: {model}")
    print(f"- API key: {masked_key(api_key)}")
    if not prompt_yes_no("Apply this configuration?"):
        warning("Cancelled.")
        return

    result: ToolConfigSetResult = tool.set_config(
        base_url=base_url,
        api_key=api_key,
        model=model,
    )
    success(f"Configuration written to: {result.target_path}")
    if result.backup_path:
        success(f"Backup saved to: {result.backup_path}")


def handle_reset(args: argparse.Namespace) -> None:
    tool, tool_name = select_tool_name(args.tool)
    backups = tool.list_backups()
    if not backups:
        error("No backups found for this tool.")
        return
    backup_to_use = backups[-1]
    if len(backups) > 1:
        header("Available backups:")
        for idx, bkp in enumerate(backups, start=1):
            print(f"{idx}) {bkp}")
        chosen = prompt_text(
            f"Select backup to restore (default {len(backups)} = latest): "
        )
        if chosen:
            if chosen.isdigit():
                idx = int(chosen)
                if 1 <= idx <= len(backups):
                    backup_to_use = backups[idx - 1]
            else:
                error("Invalid input. Using latest backup.")

    info(f"\nWill restore from backup: {backup_to_use}")
    if not prompt_yes_no("Proceed with restore?"):
        warning("Cancelled.")
        return
    target = tool.reset_config(backup_to_use)
    success(f"Restore completed. Current config: {target}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="r9s",
        description="r9s CLI: configure local tools to use the r9s API.",
    )
    subparsers = parser.add_subparsers(dest="command")

    set_parser = subparsers.add_parser("set", help="Write r9s config for a tool")
    set_parser.add_argument("tool", nargs="?", help="Tool name, e.g. claude-code")
    set_parser.add_argument("--api-key", help="API key (overrides r9s_API_KEY)")
    set_parser.add_argument("--base-url", help="Base URL (overrides r9s_BASE_URL)")
    set_parser.add_argument(
        "--model",
        help="Model name (skip interactive model selection)",
    )
    set_parser.set_defaults(func=handle_set)

    reset_parser = subparsers.add_parser("reset", help="Restore configuration from backup")
    reset_parser.add_argument("tool", nargs="?", help="Tool name, e.g. claude-code")
    reset_parser.set_defaults(func=handle_reset)
    return parser


def main(argv: Optional[Sequence[str]] = None) -> None:
    parser = build_parser()
    try:
        args = parser.parse_args(argv)
        if not getattr(args, "command", None):
            header("r9s CLI")
            info("Configure local dev tools to use r9s.")
            print()
            info("Common usage examples:")
            print("  r9s set claude-code")
            print("  r9s reset claude-code")
            print()
            info("Run 'r9s -h' to see all options.")
            return
        args.func(args)
    except KeyboardInterrupt:
        print()
        warning("Goodbye. (Interrupted by Ctrl+C)")


if __name__ == "__main__":
    main()
