from __future__ import annotations

import argparse
import sys
from typing import Optional

from r9s.cli_tools.bots import BotConfig, delete_bot, list_bots, load_bot, save_bot
from r9s.cli_tools.ui.terminal import (
    FG_RED,
    FG_YELLOW,
    error,
    header,
    info,
    prompt_text,
    success,
    warning,
)


def _require_name(name: Optional[str]) -> str:
    if name and name.strip():
        return name.strip()
    raise SystemExit("bot name is required")


def _is_interactive() -> bool:
    return sys.stdin.isatty()


def _prompt_multiline_required(message: str) -> str:
    header(message)
    first = prompt_text("> ", color=FG_YELLOW)
    while not first:
        first = prompt_text("> ", color=FG_RED)
    lines = [first]
    while True:
        line = prompt_text("> ", color=FG_YELLOW)
        if not line:
            break
        lines.append(line)
    out = "\n".join(lines).rstrip()
    if not out:
        raise SystemExit("system prompt cannot be empty")
    return out


def handle_bot_list(_: argparse.Namespace) -> None:
    bots = list_bots()
    if not bots:
        info("No bots found.")
        return
    header("Bots")
    for b in bots:
        print(f"- {b}")


def handle_bot_show(args: argparse.Namespace) -> None:
    name = _require_name(args.name)
    bot = load_bot(name)
    header(f"Bot: {bot.name}")
    if bot.description:
        print(f"- description: {bot.description}")
    if bot.system_prompt:
        print("- system_prompt: (set)")
    if bot.temperature is not None:
        print(f"- temperature: {bot.temperature}")
    if bot.top_p is not None:
        print(f"- top_p: {bot.top_p}")
    if bot.max_tokens is not None:
        print(f"- max_tokens: {bot.max_tokens}")
    if bot.presence_penalty is not None:
        print(f"- presence_penalty: {bot.presence_penalty}")
    if bot.frequency_penalty is not None:
        print(f"- frequency_penalty: {bot.frequency_penalty}")


def handle_bot_delete(args: argparse.Namespace) -> None:
    name = _require_name(args.name)
    confirm = prompt_text(f"Delete bot '{name}'? [y/N]: ", color=FG_RED).lower()
    if confirm not in ("y", "yes"):
        warning("Cancelled.")
        return
    try:
        path = delete_bot(name)
    except FileNotFoundError:
        error("Bot not found.")
        return
    success(f"Deleted: {path}")


def handle_bot_create(args: argparse.Namespace) -> None:
    name = _require_name(args.name)

    system_prompt = args.system_prompt
    if system_prompt is not None:
        system_prompt = system_prompt.strip() or None
    elif _is_interactive():
        info("Enter the system prompt for this bot.")
        system_prompt = _prompt_multiline_required(
            "System prompt (end with empty line):"
        )
    else:
        raise SystemExit("Missing --system-prompt (interactive TTY required).")

    description = (args.description or "").strip() or None

    temperature = args.temperature

    top_p = args.top_p

    max_tokens = args.max_tokens

    presence_penalty = args.presence_penalty

    frequency_penalty = args.frequency_penalty

    bot = BotConfig(
        name=name,
        description=description,
        system_prompt=system_prompt,
        temperature=temperature,
        top_p=top_p,
        max_tokens=max_tokens,
        presence_penalty=presence_penalty,
        frequency_penalty=frequency_penalty,
    )
    path = save_bot(bot)
    success(f"Saved: {path}")
