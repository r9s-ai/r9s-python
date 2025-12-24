from __future__ import annotations

import argparse
from typing import Optional

from r9s.cli_tools.bots import BotConfig, delete_bot, list_bots, load_bot, save_bot
from r9s.cli_tools.ui.terminal import (
    FG_RED,
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
    print(f"- model: {bot.model}")
    if bot.base_url:
        print(f"- base_url: {bot.base_url}")
    if bot.system_prompt_file:
        print(f"- system_prompt_file: {bot.system_prompt_file}")
    if bot.system_prompt:
        print("- system_prompt: (set)")
    if bot.lang:
        print(f"- lang: {bot.lang}")
    if bot.extensions:
        print(f"- extensions: {', '.join(bot.extensions)}")


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

    model = (args.model or "").strip()
    if not model:
        model = prompt_text("Model: ")
    while not model:
        model = prompt_text("Model cannot be empty. Model: ", color=FG_RED)

    base_url = (args.base_url or "").strip() or None
    system_prompt_file = (args.system_prompt_file or "").strip() or None
    system_prompt = args.system_prompt
    if system_prompt is not None:
        system_prompt = system_prompt.strip() or None

    lang = (args.lang or "").strip() or None
    extensions = list(args.ext or []) or None

    bot = BotConfig(
        name=name,
        model=model,
        base_url=base_url,
        system_prompt=system_prompt,
        system_prompt_file=system_prompt_file,
        lang=lang,
        extensions=extensions,
    )
    path = save_bot(bot)
    success(f"Saved: {path}")
