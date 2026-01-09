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
from r9s.cli_tools.agent_cli import (
    handle_agent_approve,
    handle_agent_audit,
    handle_agent_create,
    handle_agent_deprecate,
    handle_agent_delete,
    handle_agent_diff,
    handle_agent_export,
    handle_agent_history,
    handle_agent_import_bot,
    handle_agent_list,
    handle_agent_pull,
    handle_agent_rollback,
    handle_agent_show,
    handle_agent_update,
)
from r9s.cli_tools.command_cli import (
    handle_command_create,
    handle_command_delete,
    handle_command_list,
    handle_command_render,
    handle_command_run,
    handle_command_show,
)
from r9s.cli_tools.completion_cli import handle___complete, handle_completion
from r9s.cli_tools.chat_cli import handle_chat
from r9s.cli_tools.image_cli import handle_image_generate, handle_image_edit
from r9s.cli_tools.audio_cli import (
    handle_audio_speech,
    handle_audio_transcribe,
    handle_audio_translate,
)
from r9s.cli_tools.models_cli import handle_models_list
from r9s.cli_tools.skill_cli import (
    handle_skill_create,
    handle_skill_delete,
    handle_skill_install,
    handle_skill_list,
    handle_skill_show,
    handle_skill_validate,
)
from r9s.cli_tools.config import get_api_key, resolve_base_url, is_valid_url
from r9s.cli_tools.i18n import resolve_lang, t
from r9s.cli_tools.run_cli import handle_run
from r9s.cli_tools.tools.registry import (
    APPS,
    supported_app_names_for_config,
    supported_app_names_for_run,
)
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
        tool = APPS.resolve(ToolName(arg_name))
        if tool:
            return tool, tool.primary_name
        raise SystemExit(f"Unsupported app: {arg_name}")
    available = APPS.primary_names()
    chosen = prompt_choice(
        t("set.select_tool", lang), [str(name) for name in available]
    )
    tool = APPS.resolve(ToolName(chosen))
    if not tool:
        raise SystemExit(f"Unsupported app: {chosen}")
    return tool, tool.primary_name


def handle_game_invisible_wall(args: argparse.Namespace) -> None:
    """Handle the invisible-wall game command.

    Loads and runs the game from presets/games/invisible-wall/.
    """
    import importlib.util
    import sys
    from r9s.cli_tools.config import get_api_key, resolve_base_url

    api_key = get_api_key(args.api_key)
    if not api_key:
        error("API key required. Set R9S_API_KEY or use --api-key")
        raise SystemExit(1)

    base_url = resolve_base_url(args.base_url)

    # Find presets directory - check multiple locations
    import os
    presets_locations = []

    # 1. R9S_GAMES_DIR if set
    if os.getenv("R9S_GAMES_DIR"):
        presets_locations.append(Path(os.getenv("R9S_GAMES_DIR")) / "invisible-wall")

    # 2. Derive from R9S_SKILLS_DIR (parent/games)
    if os.getenv("R9S_SKILLS_DIR"):
        presets_locations.append(Path(os.getenv("R9S_SKILLS_DIR")).parent / "games" / "invisible-wall")

    # 3. Derive from R9S_AGENTS_DIR (parent/games)
    if os.getenv("R9S_AGENTS_DIR"):
        presets_locations.append(Path(os.getenv("R9S_AGENTS_DIR")).parent / "games" / "invisible-wall")

    # 4. Default locations
    presets_locations.extend([
        Path.home() / ".r9s" / "presets" / "games" / "invisible-wall",
        Path.home() / ".r9s" / "games" / "invisible-wall",
        Path(__file__).parent.parent.parent.parent / "presets" / "games" / "invisible-wall",
    ])

    game_path = None
    for loc in presets_locations:
        if loc.exists() and (loc / "client.py").exists():
            game_path = loc
            break

    if not game_path:
        error("Game not found. Searched locations:")
        for loc in presets_locations[:3]:
            error(f"  - {loc}")
        error("Set R9S_GAMES_DIR or install presets to ~/.r9s/presets/")
        raise SystemExit(1)

    # Add game path to sys.path for imports
    sys.path.insert(0, str(game_path))

    try:
        # Load state module first (dependency)
        state_spec = importlib.util.spec_from_file_location("state", game_path / "state.py")
        if state_spec is None or state_spec.loader is None:
            error("Failed to load state module")
            raise SystemExit(1)
        state_module = importlib.util.module_from_spec(state_spec)
        state_module.__name__ = "state"  # Ensure __name__ is set for dataclass compatibility
        sys.modules["state"] = state_module
        state_spec.loader.exec_module(state_module)

        # Load client module dynamically
        spec = importlib.util.spec_from_file_location("client", game_path / "client.py")
        if spec is None or spec.loader is None:
            error("Failed to load game client")
            raise SystemExit(1)

        client_module = importlib.util.module_from_spec(spec)
        client_module.__name__ = "client"  # Ensure __name__ is set for dataclass compatibility
        sys.modules["client"] = client_module
        spec.loader.exec_module(client_module)

        # Create character and game
        Character = client_module.Character
        InvisibleWallGame = client_module.InvisibleWallGame

        character = Character(
            name=args.name,
            university=args.university,
            major=args.major,
            year=args.year,
            gender="女",
        )

        game = InvisibleWallGame(
            api_key=api_key,
            base_url=base_url,
            model=args.model,
            consultant_model=args.consultant_model,
            character=character,
        )

        game.run()
    finally:
        # Clean up sys.path and sys.modules
        if str(game_path) in sys.path:
            sys.path.remove(str(game_path))
        sys.modules.pop("state", None)
        sys.modules.pop("client", None)


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
        description="r9s CLI: chat, manage agents, and configure local tools to use the r9s API.",
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
        help="[DEPRECATED] Bot name. Use --agent instead.",
    )
    chat_parser.add_argument(
        "--resume",
        action="store_true",
        help="Resume a saved session (interactive selection; requires TTY)",
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
        "--agent",
        help="Agent name (loads system prompt and model from ~/.r9s/agents/<agent>/)",
    )
    chat_parser.add_argument(
        "--agent-version",
        dest="agent_version",
        metavar="VERSION",
        help="Agent version to use (default: current_version from agent manifest)",
    )
    chat_parser.add_argument(
        "--var",
        action="append",
        default=[],
        help="Agent template variable (key=value, repeatable)",
    )
    chat_parser.add_argument(
        "--skill",
        action="append",
        default=[],
        help="Load skill by name (repeatable, combines with agent skills)",
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
    chat_parser.add_argument(
        "--allow-scripts",
        action="store_true",
        help="Allow skill scripts (%%{...}) to execute",
    )
    chat_parser.add_argument(
        "--rich",
        action="store_true",
        help="Enable rich markdown rendering (requires: pip install r9s[rich])",
    )
    chat_parser.epilog = (
        "Agents: `r9s chat --agent <name>` loads instructions from ~/.r9s/agents/<name>/. "
        "Skills: `r9s chat --skill <name>` loads skill instructions from ~/.r9s/skills/<name>/. "
        "Resume: `r9s chat --resume` selects a saved session under ~/.r9s/chat/. "
        "Commands: ~/.r9s/commands/*.toml are registered as /<name> in interactive chat. "
        "Template syntax: {{args}} and !{...}. Shell execution requires confirmation unless -y is provided."
    )
    chat_parser.set_defaults(func=handle_chat)

    bot_parser = subparsers.add_parser(
        "bot", help="[DEPRECATED] Use 'r9s agent' instead"
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

    agent_parser = subparsers.add_parser(
        "agent", help="Manage versioned agents (~/.r9s/agents/)"
    )
    agent_sub = agent_parser.add_subparsers(dest="agent_command")
    agent_parser.set_defaults(func=lambda _: agent_parser.print_help())

    agent_list = agent_sub.add_parser("list", help="List agents")
    agent_list.set_defaults(func=handle_agent_list)

    agent_show = agent_sub.add_parser("show", help="Show agent details")
    agent_show.add_argument("name", help="Agent name")
    agent_show.add_argument(
        "--instructions", "-i", action="store_true", help="Show full instructions"
    )
    agent_show.set_defaults(func=handle_agent_show)

    agent_create = agent_sub.add_parser("create", help="Create a new agent")
    agent_create.add_argument("name", help="Agent name")
    agent_create.add_argument("--description", help="Description (optional)")
    agent_create.add_argument("--instructions", help="Instructions text (inline)")
    agent_create.add_argument(
        "--instructions-file", "-f", help="Read instructions from file"
    )
    agent_create.add_argument(
        "--edit", "-e", action="store_true", help="Open $EDITOR to write instructions"
    )
    agent_create.add_argument("--model", help="Model name (default: R9S_MODEL)")
    agent_create.add_argument("--provider", help="Provider name (default: r9s)")
    agent_create.add_argument("--reason", help="Change reason (optional)")
    agent_create.add_argument("--params", help="Model params JSON (optional)")
    agent_create.add_argument(
        "--skill",
        action="append",
        default=[],
        help="Skill to include (repeatable)",
    )
    agent_create.set_defaults(func=handle_agent_create)

    agent_update = agent_sub.add_parser("update", help="Update agent (new version)")
    agent_update.add_argument("name", help="Agent name")
    agent_update.add_argument("--instructions", help="Instructions text (inline)")
    agent_update.add_argument(
        "--instructions-file", "-f", help="Read instructions from file"
    )
    agent_update.add_argument(
        "--edit",
        "-e",
        action="store_true",
        help="Open $EDITOR to edit instructions (pre-populated with current)",
    )
    agent_update.add_argument("--model", help="Model name (optional)")
    agent_update.add_argument("--provider", help="Provider name (optional)")
    agent_update.add_argument("--reason", help="Change reason (optional)")
    agent_update.add_argument(
        "--bump",
        choices=["patch", "minor", "major"],
        default="patch",
        help="Version bump type",
    )
    agent_update.add_argument("--params", help="Model params JSON (optional)")
    agent_update.add_argument(
        "--skill",
        action="append",
        default=None,
        help="Skill to include (repeatable, replaces existing skills)",
    )
    agent_update.set_defaults(func=handle_agent_update)

    agent_delete = agent_sub.add_parser("delete", help="Delete agent")
    agent_delete.add_argument("name", help="Agent name")
    agent_delete.set_defaults(func=handle_agent_delete)

    agent_history = agent_sub.add_parser("history", help="Show agent history")
    agent_history.add_argument("name", help="Agent name")
    agent_history.set_defaults(func=handle_agent_history)

    agent_diff = agent_sub.add_parser("diff", help="Diff two versions")
    agent_diff.add_argument("name", help="Agent name")
    agent_diff.add_argument("v1", help="Version 1")
    agent_diff.add_argument("v2", help="Version 2")
    agent_diff.set_defaults(func=handle_agent_diff)

    agent_rollback = agent_sub.add_parser("rollback", help="Rollback to version")
    agent_rollback.add_argument("name", help="Agent name")
    agent_rollback.add_argument("--version", required=True, help="Version to set")
    agent_rollback.set_defaults(func=handle_agent_rollback)

    agent_approve = agent_sub.add_parser("approve", help="Approve a version")
    agent_approve.add_argument("name", help="Agent name")
    agent_approve.add_argument("--version", required=True, help="Version to approve")
    agent_approve.set_defaults(func=handle_agent_approve)

    agent_deprecate = agent_sub.add_parser("deprecate", help="Deprecate a version")
    agent_deprecate.add_argument("name", help="Agent name")
    agent_deprecate.add_argument("--version", required=True, help="Version to deprecate")
    agent_deprecate.set_defaults(func=handle_agent_deprecate)

    agent_audit = agent_sub.add_parser("audit", help="Show audit log")
    agent_audit.add_argument("name", help="Agent name")
    agent_audit.add_argument("--last", type=int, default=None, help="Last N entries")
    agent_audit.add_argument("--request-id", help="Filter by request ID")
    agent_audit.set_defaults(func=handle_agent_audit)

    agent_export = agent_sub.add_parser("export", help="Export agent as JSON")
    agent_export.add_argument("name", help="Agent name")
    agent_export.set_defaults(func=handle_agent_export)

    agent_import_bot = agent_sub.add_parser("import-bot", help="Import bot as agent")
    agent_import_bot.add_argument("name", help="Bot name (agent name)")
    agent_import_bot.add_argument("--model", help="Model name (default: R9S_MODEL)")
    agent_import_bot.add_argument("--provider", help="Provider name (default: r9s)")
    agent_import_bot.set_defaults(func=handle_agent_import_bot)

    agent_pull = agent_sub.add_parser(
        "pull", help="Fetch an agent definition from git or HTTP"
    )
    agent_pull.add_argument(
        "ref",
        help=(
            "GitHub URL, git ref, local path, or HTTP archive URL. Examples:\n"
            "  github:owner/repo/path/to/agent\n"
            "  github:owner/repo/path/to/agent@branch\n"
            "  github:owner/repo --path path/to/agent"
        ),
    )
    agent_pull.add_argument(
        "--path", help="Optional subdirectory within the repo/archive"
    )
    agent_pull.add_argument("--name", help="Override agent name")
    agent_pull.add_argument("--force", action="store_true", help="Overwrite existing agent")
    agent_pull.set_defaults(func=handle_agent_pull)

    # Alias: 'install' as synonym for 'pull' (consistency with r9s skill install)
    agent_install = agent_sub.add_parser(
        "install", help="Install an agent from GitHub (alias for pull)"
    )
    agent_install.add_argument(
        "ref",
        help=(
            "GitHub URL or shorthand. Examples:\n"
            "  github:owner/repo/path/to/agent\n"
            "  github:owner/repo/path/to/agent@branch"
        ),
    )
    agent_install.add_argument("--name", "-n", help="Override agent name")
    agent_install.add_argument("--force", "-f", action="store_true", help="Overwrite existing agent")
    agent_install.set_defaults(func=handle_agent_pull, path=None)

    bot_delete = bot_sub.add_parser("delete", help="Delete bot")
    bot_delete.add_argument("name", help="Bot name")
    bot_delete.set_defaults(func=handle_bot_delete)

    skill_parser = subparsers.add_parser(
        "skill", help="Manage local skills (~/.r9s/skills/)"
    )
    skill_sub = skill_parser.add_subparsers(dest="skill_command")
    skill_parser.set_defaults(func=lambda _: skill_parser.print_help())

    skill_list = skill_sub.add_parser("list", help="List skills")
    skill_list.set_defaults(func=handle_skill_list)

    skill_show = skill_sub.add_parser("show", help="Show skill details")
    skill_show.add_argument("name", help="Skill name")
    skill_show.set_defaults(func=handle_skill_show)

    skill_create = skill_sub.add_parser("create", help="Create or update a skill")
    skill_create.add_argument("name", help="Skill name")
    skill_create.add_argument("--description", help="Description (optional)")
    skill_create.add_argument("--instructions", help="Instructions text (optional)")
    skill_create.add_argument("--license", help="License (optional)")
    skill_create.add_argument("--compatibility", help="Compatibility (optional)")
    skill_create.add_argument("--file", "-f", help="Load SKILL.md content from file")
    skill_create.add_argument(
        "--edit", "-e", action="store_true", help="Open $EDITOR to edit SKILL.md"
    )
    skill_create.set_defaults(func=handle_skill_create)

    skill_validate = skill_sub.add_parser("validate", help="Validate a skill")
    skill_validate.add_argument("name", help="Skill name")
    skill_validate.add_argument(
        "--allow-scripts",
        action="store_true",
        help="Allow skills that include scripts/",
    )
    skill_validate.set_defaults(func=handle_skill_validate)

    skill_delete = skill_sub.add_parser("delete", help="Delete a skill")
    skill_delete.add_argument("name", help="Skill name")
    skill_delete.set_defaults(func=handle_skill_delete)

    skill_install = skill_sub.add_parser(
        "install", help="Install a skill from GitHub"
    )
    skill_install.add_argument(
        "url",
        help=(
            "GitHub URL or shorthand. Examples:\n"
            "  github:owner/repo/path/to/skill\n"
            "  github:owner/repo/path/to/skill@branch\n"
            "  https://github.com/owner/repo/tree/branch/path"
        ),
    )
    skill_install.add_argument(
        "--name", "-n", help="Override skill name (default: derived from path)"
    )
    skill_install.add_argument(
        "--force", "-f", action="store_true", help="Overwrite existing skill"
    )
    skill_install.set_defaults(func=handle_skill_install)

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
    run_parser.epilog = f"Supported apps: {', '.join(supported_app_names_for_run())}"
    run_parser.set_defaults(func=handle_run)

    # Image generation and editing commands
    images_parser = subparsers.add_parser(
        "images", help="Generate and edit images"
    )
    images_sub = images_parser.add_subparsers(dest="images_command")
    images_parser.set_defaults(func=lambda _: images_parser.print_help())

    # r9s images generate
    images_generate = images_sub.add_parser(
        "generate", help="Generate images from text prompts"
    )
    images_generate.add_argument(
        "prompt",
        nargs="?",
        default=None,
        help="Image description prompt (or pipe via stdin)",
    )
    images_generate.add_argument(
        "-o", "--output",
        help="Output file or directory (prints URL if not specified)",
    )
    images_generate.add_argument(
        "-m", "--model",
        help="Model name (e.g., dall-e-3, gpt-image-1.5, wanx-v1)",
    )
    images_generate.add_argument(
        "-s", "--size",
        help="Image size (e.g., 1024x1024) or aspect ratio (e.g., 16:9)",
    )
    images_generate.add_argument(
        "-q", "--quality",
        choices=["standard", "hd", "low", "medium", "high"],
        help="Image quality",
    )
    images_generate.add_argument(
        "-n",
        type=int,
        default=1,
        help="Number of images to generate (1-10, model dependent)",
    )
    images_generate.add_argument(
        "--style",
        choices=["vivid", "natural"],
        help="Image style (DALL-E 3)",
    )
    images_generate.add_argument(
        "--negative-prompt",
        help="Elements to exclude from the image (Qwen, Stability)",
    )
    images_generate.add_argument(
        "--seed",
        type=int,
        help="Random seed for reproducibility",
    )
    images_generate.add_argument(
        "--prompt-extend",
        action="store_true",
        default=None,
        help="Enable AI prompt optimization (Qwen)",
    )
    images_generate.add_argument(
        "--no-prompt-extend",
        action="store_false",
        dest="prompt_extend",
        help="Disable AI prompt optimization (Qwen)",
    )
    images_generate.add_argument(
        "--watermark",
        action="store_true",
        default=None,
        help="Add watermark to generated images (Qwen)",
    )
    images_generate.add_argument(
        "--no-watermark",
        action="store_false",
        dest="watermark",
        help="Disable watermark (Qwen)",
    )
    images_generate.add_argument(
        "-f", "--format",
        choices=["url", "b64"],
        help="Response format (default: url, or b64 if -o specified)",
    )
    images_generate.add_argument(
        "--json",
        action="store_true",
        help="Output full JSON response",
    )
    images_generate.epilog = (
        "Examples:\n"
        "  r9s images generate \"A serene mountain landscape\"\n"
        "  r9s images generate \"A blue dragon\" -o dragon.png\n"
        "  r9s images generate \"A car\" -m gpt-image-1.5 -n 3 -o ./cars/\n"
        "  r9s images generate \"A forest\" --model wanx-v1 --negative-prompt \"people\"\n"
        "  cat prompt.txt | r9s images generate -o result.png"
    )
    images_generate.set_defaults(func=handle_image_generate)

    # r9s images edit
    images_edit = images_sub.add_parser(
        "edit", help="Edit an existing image using a text prompt"
    )
    images_edit.add_argument(
        "image",
        help="Path to the image file to edit (PNG, <4MB)",
    )
    images_edit.add_argument(
        "prompt",
        help="Text description of desired edit",
    )
    images_edit.add_argument(
        "-o", "--output",
        help="Output file or directory (prints URL if not specified)",
    )
    images_edit.add_argument(
        "--mask",
        help="Path to mask PNG (transparent areas indicate where to edit)",
    )
    images_edit.add_argument(
        "-m", "--model",
        help="Model name (e.g., dall-e-2)",
    )
    images_edit.add_argument(
        "-s", "--size",
        choices=["256x256", "512x512", "1024x1024"],
        help="Output size",
    )
    images_edit.add_argument(
        "-n",
        type=int,
        default=1,
        help="Number of images to generate (1-10)",
    )
    images_edit.add_argument(
        "-f", "--format",
        choices=["url", "b64"],
        help="Response format (default: url, or b64 if -o specified)",
    )
    images_edit.add_argument(
        "--json",
        action="store_true",
        help="Output full JSON response",
    )
    images_edit.epilog = (
        "Examples:\n"
        "  r9s images edit photo.png \"Add a red hat\" -o edited.png\n"
        "  r9s images edit photo.png \"Change background\" --mask mask.png -o result.png\n"
        "  r9s images edit input.png \"Make vintage\" -n 3 -o ./variations/"
    )
    images_edit.set_defaults(func=handle_image_edit)

    # Audio commands (TTS, ASR, translation)
    audio_parser = subparsers.add_parser(
        "audio", help="Text-to-speech, transcription, and translation"
    )
    audio_sub = audio_parser.add_subparsers(dest="audio_command")
    audio_parser.set_defaults(func=lambda _: audio_parser.print_help())

    # r9s audio speech (TTS)
    audio_speech = audio_sub.add_parser(
        "speech", help="Convert text to speech (TTS)"
    )
    audio_speech.add_argument(
        "text",
        nargs="?",
        default=None,
        help="Text to convert to speech (or pipe via stdin)",
    )
    audio_speech.add_argument(
        "-o", "--output",
        required=True,
        help="Output audio file path (e.g., output.mp3)",
    )
    audio_speech.add_argument(
        "-m", "--model",
        help="TTS model (overrides R9S_TTS_MODEL, default: gpt-4o-mini-tts)",
    )
    audio_speech.add_argument(
        "-v", "--voice",
        default="alloy",
        choices=["alloy", "echo", "fable", "onyx", "nova", "shimmer"],
        help="Voice type (default: alloy)",
    )
    audio_speech.add_argument(
        "-s", "--speed",
        type=float,
        help="Speech speed (0.25 to 4.0, default: 1.0)",
    )
    audio_speech.add_argument(
        "-f", "--format",
        choices=["mp3", "opus", "aac", "flac", "wav", "pcm"],
        help="Audio format (default: mp3)",
    )
    audio_speech.add_argument("--api-key", help="API key (overrides R9S_API_KEY)")
    audio_speech.add_argument("--base-url", help="Base URL (overrides R9S_BASE_URL)")
    audio_speech.epilog = (
        "Examples:\n"
        "  r9s audio speech \"Hello world\" -o hello.mp3\n"
        "  r9s audio speech \"Welcome\" -o welcome.wav -v nova -f wav\n"
        "  echo \"Hello\" | r9s audio speech -o hello.mp3"
    )
    audio_speech.set_defaults(func=handle_audio_speech)

    # r9s audio transcribe (ASR)
    audio_transcribe = audio_sub.add_parser(
        "transcribe", help="Transcribe audio to text (ASR)"
    )
    audio_transcribe.add_argument(
        "audio",
        help="Audio file to transcribe",
    )
    audio_transcribe.add_argument(
        "-o", "--output",
        help="Output text file (prints to stdout if not specified)",
    )
    audio_transcribe.add_argument(
        "-m", "--model",
        help="ASR model (overrides R9S_STT_MODEL, default: whisper-1)",
    )
    audio_transcribe.add_argument(
        "-l", "--language",
        help="Audio language (ISO-639-1 code, e.g., en, zh, ja)",
    )
    audio_transcribe.add_argument(
        "-p", "--prompt",
        help="Optional prompt to guide transcription style",
    )
    audio_transcribe.add_argument(
        "-f", "--format",
        choices=["json", "text", "srt", "verbose_json", "vtt"],
        help="Output format (default: json)",
    )
    audio_transcribe.add_argument("--api-key", help="API key (overrides R9S_API_KEY)")
    audio_transcribe.add_argument("--base-url", help="Base URL (overrides R9S_BASE_URL)")
    audio_transcribe.epilog = (
        "Examples:\n"
        "  r9s audio transcribe recording.mp3\n"
        "  r9s audio transcribe meeting.wav -o transcript.txt -f text\n"
        "  r9s audio transcribe audio.mp3 -l zh -o chinese.srt -f srt"
    )
    audio_transcribe.set_defaults(func=handle_audio_transcribe)

    # r9s audio translate
    audio_translate = audio_sub.add_parser(
        "translate", help="Translate audio to English text"
    )
    audio_translate.add_argument(
        "audio",
        help="Audio file to translate",
    )
    audio_translate.add_argument(
        "-o", "--output",
        help="Output text file (prints to stdout if not specified)",
    )
    audio_translate.add_argument(
        "-m", "--model",
        help="Model (overrides R9S_STT_MODEL, default: whisper-1)",
    )
    audio_translate.add_argument(
        "-p", "--prompt",
        help="Optional prompt to guide translation style",
    )
    audio_translate.add_argument(
        "-f", "--format",
        choices=["json", "text"],
        help="Output format (default: json)",
    )
    audio_translate.add_argument("--api-key", help="API key (overrides R9S_API_KEY)")
    audio_translate.add_argument("--base-url", help="Base URL (overrides R9S_BASE_URL)")
    audio_translate.epilog = (
        "Examples:\n"
        "  r9s audio translate chinese_speech.mp3\n"
        "  r9s audio translate french_audio.wav -o english.txt -f text"
    )
    audio_translate.set_defaults(func=handle_audio_translate)

    # Game command (Invisible Wall)
    game_parser = subparsers.add_parser(
        "game", help="Play interactive games (SDK demos)"
    )
    game_sub = game_parser.add_subparsers(dest="game_command")

    # Invisible Wall game
    iw_parser = game_sub.add_parser(
        "invisible-wall",
        aliases=["iw"],
        help="The Invisible Wall - 关系模拟器",
    )
    iw_parser.add_argument("--name", default="林小晚", help="她的名字")
    iw_parser.add_argument("--university", default="浙江大学", help="学校")
    iw_parser.add_argument("--major", default="中文系", help="专业")
    iw_parser.add_argument("--year", default="大三", help="年级")
    iw_parser.add_argument("--model", default="gpt-5-mini", help="Character model")
    iw_parser.add_argument("--consultant-model", default="glm-4.7", help="Consultant AI model")
    iw_parser.add_argument("--api-key", help="API key (or set R9S_API_KEY)")
    iw_parser.add_argument("--base-url", help="Base URL (or set R9S_BASE_URL)")
    iw_parser.set_defaults(func=handle_game_invisible_wall)

    # Models command
    models_parser = subparsers.add_parser(
        "models", help="List available models from the API"
    )
    models_parser.add_argument("--api-key", help="API key (overrides R9S_API_KEY)")
    models_parser.add_argument("--base-url", help="Base URL (overrides R9S_BASE_URL)")
    models_parser.add_argument(
        "--details", "-d", action="store_true", help="Show model details (owner, created)"
    )
    models_parser.add_argument(
        "--lang",
        default=None,
        help="UI language (default: en; can also set R9S_LANG). Supported: en, zh-CN",
    )
    models_parser.set_defaults(func=handle_models_list)

    set_parser = subparsers.add_parser("set", help="Write r9s config for an app")
    set_parser.add_argument(
        "--lang",
        default=None,
        help="UI language (default: en; can also set R9S_LANG). Supported: en, zh-CN",
    )
    supported_apps = ", ".join(supported_app_names_for_config())
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

    completion_parser = subparsers.add_parser(
        "completion", help="Generate shell completion scripts"
    )
    completion_parser.add_argument(
        "shell",
        nargs="?",
        default="bash",
        help="Shell name (bash; planned: zsh, fish)",
    )
    completion_parser.set_defaults(func=handle_completion)

    complete_parser = subparsers.add_parser("__complete", help=argparse.SUPPRESS)
    complete_parser.add_argument("shell", help=argparse.SUPPRESS)
    complete_parser.add_argument("cword", type=int, help=argparse.SUPPRESS)
    complete_parser.add_argument("words", nargs=argparse.REMAINDER, help=argparse.SUPPRESS)
    complete_parser.set_defaults(func=handle___complete)
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
            apps_run = ", ".join(supported_app_names_for_run())
            apps_config = ", ".join(supported_app_names_for_config())
            print_home(
                name=t("cli.title", lang),
                description=t("cli.tagline", lang),
                examples_title=t("cli.examples.title", lang),
                examples=[
                    t("cli.examples.chat_interactive", lang),
                    t("cli.examples.chat_pipe", lang),
                    t("cli.examples.chat_pipe_image", lang),
                    t("cli.examples.resume", lang),
                    t("cli.examples.agents", lang),
                    t("cli.examples.run", lang, apps=apps_run),
                    t("cli.examples.configure", lang, apps=apps_config),
                ],
                footer=t("cli.examples.more", lang),
            )
            return
        args.func(args)
    except KeyboardInterrupt:
        print()
        warning("Goodbye. (Interrupted by Ctrl+C)")
    except EOFError:
        # Treat Ctrl+D / closed stdin as a graceful exit in interactive flows.
        print()
        return


if __name__ == "__main__":
    main()
