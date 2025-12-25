import argparse
import json
import os
import urllib.error
import urllib.request
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Tuple

try:
    from dotenv import load_dotenv  # pyright: ignore[reportMissingImports]
except Exception:  # pragma: no cover
    load_dotenv = None  # type: ignore[assignment]

from r9s.cli_tools.bot_cli import (
    handle_bot_create,
    handle_bot_delete,
    handle_bot_list,
    handle_bot_show,
)
from r9s.cli_tools.command_cli import (
    handle_command_create,
    handle_command_delete,
    handle_command_list,
    handle_command_render,
    handle_command_run,
    handle_command_show,
)
from r9s.cli_tools.chat_cli import handle_chat
from r9s.cli_tools.config import get_api_key, resolve_base_url, is_valid_url
from r9s.cli_tools.i18n import resolve_lang, t
from r9s.cli_tools.run_cli import handle_run
from r9s.cli_tools.ui.banner import CLI_BANNER
from r9s.cli_tools.ui.prompts import prompt_choice, prompt_yes_no
from r9s.cli_tools.ui.spinner import LoadingSpinner
from r9s.cli_tools.ui.home import print_home
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
from r9s.cli_tools.tools.codex import CodexIntegration
from r9s.cli_tools.tools.qwen_code import QwenCodeIntegration


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

_codex = CodexIntegration()
for alias in _codex.aliases:
    TOOLS.register(ToolName(alias), _codex)

_qwen_code = QwenCodeIntegration()
for alias in _qwen_code.aliases:
    TOOLS.register(ToolName(alias), _qwen_code)


def masked_key(key: str, visible: int = 4) -> str:
    if len(key) <= visible:
        return "*" * len(key)
    return f"{key[:visible]}***{key[-visible:]}"


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
    base_url: str,
    api_key: str,
    preset: Optional[str],
    lang: str,
    tool_name: str = "claude-code",
) -> tuple[str, List[str]]:
    """Choose a model and return both the choice and the fetched model list."""
    if preset:
        return preset, []
    models = fetch_models(base_url, api_key)
    if models:
        info(t("set.available_models", lang))
        # Use tool-specific prompt text
        if tool_name == "codex":
            prompt_text_key = "Select model"
        elif tool_name == "qwen-code":
            prompt_text_key = "Select model"
        else:
            prompt_text_key = t("set.select_model", lang)
        choice = prompt_choice(prompt_text_key, models)
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


def resolve_base_url_with_validation(preset: Optional[str]) -> str:
    """Get and validate base_url, prioritizing environment variable."""
    # 1. If provided via command-line argument, validate and use
    if preset:
        if is_valid_url(preset):
            return preset.rstrip("/")
        error(f"Invalid base_url format: {preset}")

    # 2. Try reading from environment variable
    env_url = os.getenv("R9S_BASE_URL")
    if env_url and is_valid_url(env_url):
        info(f"Using R9S_BASE_URL from environment: {env_url}")
        return env_url.rstrip("/")

    # 3. Prompt user for manual input
    while True:
        url = prompt_text("R9S_BASE_URL is not set or invalid. Enter base URL: ")
        if is_valid_url(url):
            return url.rstrip("/")
        error("Invalid URL format. Must start with http:// or https://")


def supports_reasoning(model_name: str) -> bool:
    """Check if model supports reasoning_effort parameter."""
    reasoning_keywords = ["reasoning", "o1", "o3", "think", "reason", "extended"]
    model_lower = model_name.lower()
    return any(keyword in model_lower for keyword in reasoning_keywords)


def select_tool_name(arg_name: Optional[str], lang: str) -> Tuple[ToolIntegration, str]:
    if arg_name:
        if arg_name.strip().lower() == "cc":
            arg_name = "claude-code"
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
    tool, tool_name = select_tool_name(args.app, lang)
    api_key = resolve_api_key(args.api_key)

    # Get base_url with default fallback (https://api.huamedia.tv/v1)
    base_url = resolve_base_url(args.base_url)
    # Validate the URL format - should always be valid with default fallback
    if not is_valid_url(base_url):
        # This should rarely happen unless user explicitly set invalid URL
        error(f"Invalid base_url format: '{base_url}'")
        error(
            "Please set a valid R9S_BASE_URL environment variable or use --base-url parameter"
        )
        raise SystemExit(1)

    model, cached_models = choose_model(
        base_url, api_key, args.model, lang, tool.primary_name
    )

    # Small model selection - skip for codex and qwen-code
    small_model = ""
    if tool.primary_name not in ("codex", "qwen-code"):
        small_model = choose_small_model(base_url, api_key, model, cached_models, lang)

    # Codex-specific configuration
    wire_api = "responses"  # default
    reasoning_effort = None

    if tool.primary_name == "codex":
        # Select wire_api type
        info("\nSelect wire API type:")
        wire_api = prompt_choice(
            "Choose API protocol", ["responses", "chat", "completion"]
        )

        # Check if model supports reasoning_effort
        if supports_reasoning(model):
            info(f"\nModel '{model}' appears to support reasoning effort.")
            if prompt_yes_no("Configure reasoning effort?", default_no=True):
                reasoning_effort = prompt_choice(
                    "Select reasoning effort level", ["low", "medium", "high"]
                )

    # Get config file path from tool if available
    config_path = getattr(tool, "_settings_path", None)

    header(t("set.summary_header", lang))
    print(t("set.summary_tool", lang, tool=tool_name))
    if config_path:
        print(t("set.summary_config_file", lang, path=config_path))
    print(t("set.summary_base_url", lang, url=base_url))
    print(t("set.summary_main_model", lang, model=model))
    if tool.primary_name not in ("codex", "qwen-code"):
        print(t("set.summary_small_model", lang, model=small_model))
    if tool.primary_name == "codex":
        print(f"Wire API: {wire_api}")
        if reasoning_effort:
            print(f"Reasoning effort: {reasoning_effort}")
    if tool.primary_name == "qwen-code":
        print(f"Config files: {config_path}, ~/.qwen/.env")
    print(t("set.summary_api_key", lang, apikey=masked_key(api_key)))
    if not prompt_yes_no(t("set.confirm_apply", lang)):
        warning(t("set.cancelled", lang))
        return

    # Call set_config with appropriate parameters based on tool type
    if tool.primary_name == "codex":
        # Codex requires wire_api and optional reasoning_effort
        result: ToolConfigSetResult = tool.set_config(
            base_url=base_url,
            api_key=api_key,
            model=model,
            small_model=small_model,
            wire_api=wire_api,
            reasoning_effort=reasoning_effort,
        )
    else:
        # Claude Code and other tools use standard parameters
        result = tool.set_config(
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
    tool, tool_name = select_tool_name(args.app, lang)
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
        "bot",
        nargs="?",
        default=None,
        help="Bot name (loads system_prompt from ~/.r9s/bots/<bot>.toml). Use `resume` to resume a session.",
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
        "--system-prompt", help="System prompt text (overrides R9S_SYSTEM_PROMPT)"
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
    chat_parser.add_argument(
        "-y",
        "--yes",
        action="store_true",
        help="Skip confirmation for template shell execution (!{...})",
    )
    chat_parser.epilog = (
        "Bots: `r9s chat <bot>` loads system_prompt from ~/.r9s/bots/<bot>.toml. "
        "Commands: ~/.r9s/commands/*.toml are registered as /<name> in interactive chat. "
        "Template syntax: {{args}} and !{...}. Shell execution requires confirmation unless -y is provided."
    )
    chat_parser.set_defaults(func=handle_chat)

    bot_parser = subparsers.add_parser(
        "bot", help="Manage local bots (~/.r9s/bots/*.toml)"
    )
    bot_sub = bot_parser.add_subparsers(dest="bot_command")
    bot_parser.set_defaults(func=lambda _: bot_parser.print_help())

    bot_create = bot_sub.add_parser("create", help="Create or update a bot")
    bot_create.add_argument("name", help="Bot name")
    bot_create.add_argument("--description", help="Description (prompts if omitted)")
    bot_create.add_argument(
        "--system-prompt", help="System prompt text (prompts if omitted)"
    )
    bot_create.add_argument(
        "--temperature",
        type=float,
        default=None,
        help="Sampling temperature (optional)",
    )
    bot_create.add_argument(
        "--top-p", type=float, default=None, help="Top-p (optional)"
    )
    bot_create.add_argument(
        "--max-tokens", type=int, default=None, help="Max tokens (optional)"
    )
    bot_create.add_argument(
        "--presence-penalty",
        type=float,
        default=None,
        help="Presence penalty (optional)",
    )
    bot_create.add_argument(
        "--frequency-penalty",
        type=float,
        default=None,
        help="Frequency penalty (optional)",
    )
    bot_create.epilog = "Bots are saved as TOML under ~/.r9s/bots/<name>.toml and only contain system_prompt."
    bot_create.set_defaults(func=handle_bot_create)

    bot_list = bot_sub.add_parser("list", help="List bots")
    bot_list.set_defaults(func=handle_bot_list)

    bot_show = bot_sub.add_parser("show", help="Show bot config")
    bot_show.add_argument("name", help="Bot name")
    bot_show.set_defaults(func=handle_bot_show)

    bot_delete = bot_sub.add_parser("delete", help="Delete bot")
    bot_delete.add_argument("name", help="Bot name")
    bot_delete.set_defaults(func=handle_bot_delete)

    command_parser = subparsers.add_parser(
        "command", help="Manage local commands (~/.r9s/commands/*.toml)"
    )
    command_sub = command_parser.add_subparsers(dest="command_command")
    command_parser.set_defaults(func=lambda _: command_parser.print_help())

    command_create = command_sub.add_parser("create", help="Create or update a command")
    command_create.add_argument("name", help="Command name")
    command_create.add_argument(
        "--description", help="Description (prompts if omitted)"
    )
    command_create.add_argument(
        "--prompt", help="Prompt template text (prompts if omitted)"
    )
    command_create.add_argument(
        "--prompt-file", type=Path, help="Prompt template file path"
    )
    command_create.set_defaults(func=handle_command_create)

    command_list = command_sub.add_parser("list", help="List commands")
    command_list.set_defaults(func=handle_command_list)

    command_show = command_sub.add_parser("show", help="Show command config")
    command_show.add_argument("name", help="Command name")
    command_show.set_defaults(func=handle_command_show)

    command_delete = command_sub.add_parser("delete", help="Delete command")
    command_delete.add_argument("name", help="Command name")
    command_delete.set_defaults(func=handle_command_delete)

    command_render = command_sub.add_parser("render", help="Render a command prompt")
    command_render.add_argument("name", help="Command name")
    command_render.add_argument(
        "-y",
        "--yes",
        action="store_true",
        help="Skip confirmation for template shell execution (!{...})",
    )
    command_render.add_argument(
        "args", nargs=argparse.REMAINDER, help="Arguments for {{args}}"
    )
    command_render.set_defaults(func=handle_command_render)

    command_run = command_sub.add_parser("run", help="Run a command (single-turn)")
    command_run.add_argument("name", help="Command name")
    command_run.add_argument("--bot", help="Bot name (load system_prompt)")
    command_run.add_argument("--lang", default=None, help="UI language (en, zh-CN)")
    command_run.add_argument("--api-key", help="API key (overrides R9S_API_KEY)")
    command_run.add_argument("--base-url", help="Base URL (overrides R9S_BASE_URL)")
    command_run.add_argument("--model", help="Model name (overrides R9S_MODEL)")
    command_run.add_argument(
        "--no-stream",
        action="store_true",
        help="Disable streaming output",
    )
    command_run.add_argument(
        "-y",
        "--yes",
        action="store_true",
        help="Skip confirmation for template shell execution (!{...})",
    )
    command_run.add_argument(
        "args", nargs=argparse.REMAINDER, help="Arguments for {{args}}"
    )
    command_run.set_defaults(func=handle_command_run)

    run_parser = subparsers.add_parser("run", help="Run an app with r9s env injected")
    run_parser.add_argument("app", help="App name (e.g. claude-code)")
    run_parser.add_argument("--api-key", help="API key (overrides R9S_API_KEY)")
    run_parser.add_argument("--base-url", help="Base URL (overrides R9S_BASE_URL)")
    run_parser.add_argument("--model", help="Model name (overrides R9S_MODEL)")
    run_parser.add_argument(
        "--print-env",
        action="store_true",
        help="Print the injected env and exit",
    )
    run_parser.add_argument(
        "--confirm",
        action="store_true",
        help="Ask for confirmation before running",
    )
    run_parser.add_argument(
        "args",
        nargs=argparse.REMAINDER,
        help="Arguments passed to the underlying command (use `--` to separate)",
    )
    run_parser.set_defaults(func=handle_run)

    set_parser = subparsers.add_parser("set", help="Write r9s config for a tool")
    set_parser.add_argument(
        "--lang",
        default=None,
        help="UI language (default: en; can also set R9S_LANG). Supported: en, zh-CN",
    )
    primary_apps = [str(x) for x in TOOLS.primary_names()]
    supported_set = set(primary_apps)
    if "claude-code" in supported_set:
        supported_set.add("cc")
    supported_apps = ", ".join(sorted(supported_set))
    set_parser.epilog = f"Supported apps: {supported_apps}"
    set_parser.add_argument("app", nargs="?", help="App name, e.g. claude-code")
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
    reset_parser.epilog = f"Supported apps: {supported_apps}"
    reset_parser.add_argument("app", nargs="?", help="App name, e.g. claude-code")
    reset_parser.set_defaults(func=handle_reset)
    return parser


def main(argv: Optional[Sequence[str]] = None) -> None:
    parser = build_parser()
    try:
        # Load `.env` from current working directory (best-effort).
        # Disable with: R9S_NO_DOTENV=1
        if load_dotenv is not None and not os.getenv("R9S_NO_DOTENV"):
            load_dotenv(dotenv_path=Path.cwd() / ".env", override=False)

        args = parser.parse_args(argv)

        maybe_notify_update()
        if not getattr(args, "command", None):
            lang = resolve_lang(getattr(args, "lang", None))
            print(_style(CLI_BANNER, FG_CYAN))
            print()
            print_home(
                name=t("cli.title", lang),
                description=t("cli.tagline", lang),
                examples_title=t("cli.examples.title", lang),
                examples=[
                    t("cli.examples.chat_interactive", lang),
                    t("cli.examples.chat_pipe", lang),
                    t("cli.examples.resume", lang),
                    t("cli.examples.bots", lang),
                    t("cli.examples.run", lang),
                    t("cli.examples.configure", lang),
                ],
                footer=t("cli.examples.more", lang),
            )
            return
        args.func(args)
    except KeyboardInterrupt:
        print()
        warning("Goodbye. (Interrupted by Ctrl+C)")


if __name__ == "__main__":
    main()
