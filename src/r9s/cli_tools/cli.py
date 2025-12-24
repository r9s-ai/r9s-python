import argparse
import json
import sys
import threading
import time
import urllib.error
import urllib.request
from typing import Dict, List, Optional, Sequence, Tuple

from r9s.cli_tools.bot_cli import (
    handle_bot_create,
    handle_bot_delete,
    handle_bot_list,
    handle_bot_show,
)
from r9s.cli_tools.chat_cli import handle_chat
from r9s.cli_tools.config import get_api_key, resolve_base_url
from r9s.cli_tools.i18n import resolve_lang, t
from r9s.cli_tools.ui.terminal import (
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
from r9s.cli_tools.update_check import maybe_notify_update
from r9s.cli_tools.tools.base import ToolConfigSetResult, ToolIntegration
from r9s.cli_tools.tools.claude_code import ClaudeCodeIntegration


class ToolRegistry:
    def __init__(self) -> None:
        self._registry: Dict[ToolName, ToolIntegration] = {}

    def register(self, name: ToolName, tool: ToolIntegration) -> None:
        self._registry[name] = tool

    def get(self, name: ToolName) -> Optional[ToolIntegration]:
        return self._registry.get(name)

    def primary_names(self) -> List[ToolName]:
        names = sorted({str(tool.primary_name) for tool in self._registry.values()})
        return [ToolName(name) for name in names]

    def resolve(self, name: ToolName) -> Optional[ToolIntegration]:
        if name in self._registry:
            return self._registry[name]
        normalized = name.lower().replace("_", "-")
        return self._registry.get(ToolName(normalized))


TOOLS = ToolRegistry()
_claude_code = ClaudeCodeIntegration()
for alias in _claude_code.aliases:
    TOOLS.register(ToolName(alias), _claude_code)


def masked_key(key: str, visible: int = 4) -> str:
    if len(key) <= visible:
        return "*" * len(key)
    return f"{key[:visible]}***{key[-visible:]}"


class LoadingSpinner:
    """Context manager for displaying a loading animation."""

    def __init__(self, message: str = "Loading"):
        self.message = message
        self.running = False
        self.thread = None

    def _animate(self):
        dots = 0
        while self.running:
            # Print message with animated dots (0-3 dots)
            sys.stdout.write(f"\r{self.message}{'.' * dots}   ")
            sys.stdout.flush()
            dots = (dots + 1) % 4
            time.sleep(0.5)
        # Clear the line when done
        sys.stdout.write("\r" + " " * (len(self.message) + 10) + "\r")
        sys.stdout.flush()

    def __enter__(self):
        self.running = True
        self.thread = threading.Thread(target=self._animate, daemon=True)
        self.thread.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.running = False
        if self.thread:
            self.thread.join(timeout=1)


def prompt_choice(prompt: str, options: List[str], show_options: bool = True) -> str:
    # Calculate width needed for numbers (e.g., "10)" needs 3 chars)
    max_num_width = len(f"{len(options)})")
    if show_options:
        for idx, value in enumerate(options, start=1):
            num_str = f"{idx})"
            # Right-align the number part for consistent spacing
            print(_style(num_str.rjust(max_num_width), FG_CYAN), value)
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
    url = base_url.rstrip("/") + "/models"
    headers = {"Authorization": f"Bearer {api_key}"}
    req = urllib.request.Request(url, headers=headers)

    with LoadingSpinner("Fetching models"):
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
            error(
                "Model list response is not valid JSON. Skipping automatic selection."
            )
            return []

    if isinstance(data, list) and all(isinstance(item, str) for item in data):
        return sorted(data)
    if isinstance(data, dict) and "data" in data and isinstance(data["data"], list):
        models = []
        for item in data["data"]:
            if isinstance(item, dict) and "id" in item:
                models.append(str(item["id"]))
            elif isinstance(item, str):
                models.append(item)
        return sorted(models)
    error("Could not parse model list from response. Please enter a model manually.")
    return []


def choose_model(
    base_url: str, api_key: str, preset: Optional[str], lang: str
) -> tuple[str, List[str]]:
    """Choose a model and return both the choice and the fetched model list."""
    if preset:
        return preset, []
    models = fetch_models(base_url, api_key)
    if models:
        info(t("set.available_models", lang))
        choice = prompt_choice(t("set.select_model", lang), models)
        return choice, models
    manual = prompt_text(t("set.enter_model", lang))
    while not manual:
        manual = prompt_text(t("set.enter_model_empty", lang), color=FG_RED)
    return manual, []


def choose_small_model(
    base_url: str, api_key: str, main_model: str, cached_models: List[str], lang: str
) -> str:
    """Choose small/fast model directly from model list or manual input.

    Args:
        cached_models: Previously fetched model list. If empty, prompts for manual input instead.
    """
    # If we have cached models, show them for selection (without reprinting the list)
    if cached_models:
        return prompt_choice(
            t("set.select_small_model", lang), cached_models, show_options=False
        )

    # Otherwise, prompt for manual input (main model was entered manually)
    manual = prompt_text(t("set.enter_small_model", lang))
    while not manual:
        manual = prompt_text(t("set.enter_small_model_empty", lang), color=FG_RED)
    return manual


def resolve_api_key(preset: Optional[str]) -> str:
    env_or_arg = get_api_key(preset)
    if env_or_arg:
        return env_or_arg
    key = prompt_secret("R9S_API_KEY is not set. Enter API key: ")
    while not key:
        key = prompt_secret("API key cannot be empty. Enter API key: ", color=FG_RED)
    return key


def select_tool_name(arg_name: Optional[str], lang: str) -> Tuple[ToolIntegration, str]:
    if arg_name:
        tool = TOOLS.resolve(ToolName(arg_name))
        if tool:
            return tool, tool.primary_name
        raise SystemExit(f"Unsupported tool: {arg_name}")
    available = TOOLS.primary_names()
    chosen = prompt_choice(
        t("set.select_tool", lang), [str(name) for name in available]
    )
    tool = TOOLS.resolve(ToolName(chosen))
    if not tool:
        raise SystemExit(f"Unsupported tool: {chosen}")
    return tool, tool.primary_name


def handle_set(args: argparse.Namespace) -> None:
    lang = resolve_lang(getattr(args, "lang", None))
    tool, tool_name = select_tool_name(args.tool, lang)
    api_key = resolve_api_key(args.api_key)
    base_url = resolve_base_url(args.base_url)
    model, cached_models = choose_model(base_url, api_key, args.model, lang)
    small_model = choose_small_model(base_url, api_key, model, cached_models, lang)

    # Get config file path from tool if available
    config_path = getattr(tool, "_settings_path", None)

    header(t("set.summary_header", lang))
    print(t("set.summary_tool", lang, tool=tool_name))
    if config_path:
        print(t("set.summary_config_file", lang, path=config_path))
    print(t("set.summary_base_url", lang, url=base_url))
    print(t("set.summary_main_model", lang, model=model))
    print(t("set.summary_small_model", lang, model=small_model))
    print(t("set.summary_api_key", lang, apikey=masked_key(api_key)))
    if not prompt_yes_no(t("set.confirm_apply", lang)):
        warning(t("set.cancelled", lang))
        return

    result: ToolConfigSetResult = tool.set_config(
        base_url=base_url,
        api_key=api_key,
        model=model,
        small_model=small_model,
    )
    success(t("set.success_written", lang, path=result.target_path))
    if result.backup_path:
        success(t("set.success_backup", lang, path=result.backup_path))


def handle_reset(args: argparse.Namespace) -> None:
    lang = resolve_lang(getattr(args, "lang", None))
    tool, tool_name = select_tool_name(args.tool, lang)
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
        description="r9s CLI: chat, manage bots, and configure local tools to use the r9s API.",
    )
    parser.add_argument(
        "--lang",
        default=None,
        help="UI language (default: en; can also set R9S_LANG). Supported: en, zh-CN",
    )
    subparsers = parser.add_subparsers(dest="command")

    chat_parser = subparsers.add_parser(
        "chat", help="Interactive chat (supports piping stdin)"
    )
    chat_parser.add_argument(
        "action",
        nargs="?",
        choices=["resume"],
        help="Special actions (e.g. resume a saved session)",
    )
    chat_parser.add_argument(
        "--lang",
        default=None,
        help="UI language (default: en; can also set R9S_LANG). Supported: en, zh-CN",
    )
    chat_parser.add_argument("--api-key", help="API key (overrides R9S_API_KEY)")
    chat_parser.add_argument("--base-url", help="Base URL (overrides R9S_BASE_URL)")
    chat_parser.add_argument("--model", help="Model name (overrides R9S_MODEL)")
    chat_parser.add_argument(
        "--bot", help="Bot name (load defaults from ~/.r9s/bots/<bot>.json)"
    )
    chat_parser.add_argument(
        "--system-prompt", help="System prompt text (overrides R9S_SYSTEM_PROMPT)"
    )
    chat_parser.add_argument(
        "--system-prompt-file", help="Load system prompt from file"
    )
    chat_parser.add_argument(
        "--history-file",
        help="History file path (default: auto under ~/.r9s/; disabled when --no-history)",
    )
    chat_parser.add_argument(
        "--no-history",
        action="store_true",
        help="Disable history persistence (no load/save)",
    )
    chat_parser.add_argument(
        "--ext",
        action="append",
        default=[],
        help="Chat extension module path or .py file (repeatable; or use R9S_CHAT_EXTENSIONS)",
    )
    chat_parser.add_argument(
        "--no-stream",
        action="store_true",
        help="Disable streaming output",
    )
    chat_parser.set_defaults(func=handle_chat)

    bot_parser = subparsers.add_parser("bot", help="Manage local bots (~/.r9s/bots)")
    bot_sub = bot_parser.add_subparsers(dest="bot_command")

    bot_create = bot_sub.add_parser("create", help="Create or update a bot")
    bot_create.add_argument("name", help="Bot name")
    bot_create.add_argument("--model", help="Model name")
    bot_create.add_argument("--base-url", help="Base URL")
    bot_create.add_argument("--system-prompt", help="System prompt text")
    bot_create.add_argument("--system-prompt-file", help="System prompt file path")
    bot_create.add_argument("--lang", help="Default UI language (en, zh-CN)")
    bot_create.add_argument(
        "--ext", action="append", default=[], help="Default chat extension (repeatable)"
    )
    bot_create.set_defaults(func=handle_bot_create)

    bot_list = bot_sub.add_parser("list", help="List bots")
    bot_list.set_defaults(func=handle_bot_list)

    bot_show = bot_sub.add_parser("show", help="Show bot config")
    bot_show.add_argument("name", help="Bot name")
    bot_show.set_defaults(func=handle_bot_show)

    bot_delete = bot_sub.add_parser("delete", help="Delete bot")
    bot_delete.add_argument("name", help="Bot name")
    bot_delete.set_defaults(func=handle_bot_delete)

    set_parser = subparsers.add_parser("set", help="Write r9s config for a tool")
    set_parser.add_argument(
        "--lang",
        default=None,
        help="UI language (default: en; can also set R9S_LANG). Supported: en, zh-CN",
    )
    set_parser.add_argument("tool", nargs="?", help="Tool name, e.g. claude-code")
    set_parser.add_argument("--api-key", help="API key (overrides R9S_API_KEY)")
    set_parser.add_argument("--base-url", help="Base URL (overrides R9S_BASE_URL)")
    set_parser.add_argument(
        "--model",
        help="Model name (skip interactive model selection)",
    )
    set_parser.set_defaults(func=handle_set)

    reset_parser = subparsers.add_parser(
        "reset", help="Restore configuration from backup"
    )
    reset_parser.add_argument(
        "--lang",
        default=None,
        help="UI language (default: en; can also set R9S_LANG). Supported: en, zh-CN",
    )
    reset_parser.add_argument("tool", nargs="?", help="Tool name, e.g. claude-code")
    reset_parser.set_defaults(func=handle_reset)
    return parser


def main(argv: Optional[Sequence[str]] = None) -> None:
    parser = build_parser()
    try:
        args = parser.parse_args(argv)
        maybe_notify_update()
        if not getattr(args, "command", None):
            lang = resolve_lang(getattr(args, "lang", None))
            print(_style(t("cli.banner", lang), FG_CYAN))
            info(t("cli.tagline", lang))
            print()
            info(t("cli.examples.title", lang))
            print(t("cli.examples.chat_interactive", lang))
            print()
            print(t("cli.examples.chat_pipe", lang))
            print()
            print(t("cli.examples.resume", lang))
            print()
            print(t("cli.examples.bots", lang))
            print()
            print(t("cli.examples.configure", lang))
            print()
            info(t("cli.examples.more", lang))
            return
        args.func(args)
    except KeyboardInterrupt:
        print()
        warning("Goodbye. (Interrupted by Ctrl+C)")


if __name__ == "__main__":
    main()
