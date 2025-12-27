from __future__ import annotations

import argparse
import json
import sys
from typing import Any
from typing import Optional, cast

from r9s import models
from r9s.cli_tools.commands import (
    CommandConfig,
    delete_command,
    list_commands,
    load_command,
    save_command,
)
from r9s.cli_tools.template_renderer import RenderContext, render_template
from r9s.cli_tools.bots import load_bot
from r9s.cli_tools.config import (
    get_api_key,
    resolve_base_url,
    resolve_model,
    resolve_system_prompt,
)
from r9s.cli_tools.i18n import resolve_lang, t
from r9s.sdk import R9S
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
from r9s.cli_tools.ui.spinner import Spinner


def _require_name(name: Optional[str]) -> str:
    if name and name.strip():
        return name.strip()
    raise SystemExit("command name is required")


def _is_interactive() -> bool:
    return sys.stdin.isatty()


def _prompt_optional(message: str) -> Optional[str]:
    value = prompt_text(message).strip()
    return value or None


def _prompt_multiline_required(message: str, *, hint: Optional[str] = None) -> str:
    header(message)
    if hint:
        info(hint)
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
        raise SystemExit("prompt cannot be empty")
    return out


def handle_command_list(_: argparse.Namespace) -> None:
    cmds = list_commands()
    if not cmds:
        info("No commands found.")
        return
    header("Commands")
    for c in cmds:
        print(f"- {c}")


def handle_command_show(args: argparse.Namespace) -> None:
    name = _require_name(args.name)
    cmd = load_command(name)
    header(f"Command: {cmd.name}")
    if cmd.description:
        print(f"- description: {cmd.description}")
    print("- prompt: (set)")


def handle_command_delete(args: argparse.Namespace) -> None:
    name = _require_name(args.name)
    confirm = prompt_text(f"Delete command '{name}'? [y/N]: ", color=FG_RED).lower()
    if confirm not in ("y", "yes"):
        warning("Cancelled.")
        return
    try:
        path = delete_command(name)
    except FileNotFoundError:
        error("Command not found.")
        return
    success(f"Deleted: {path}")


def handle_command_create(args: argparse.Namespace) -> None:
    name = _require_name(args.name)

    description = (args.description or "").strip() or None
    if description is None and _is_interactive():
        description = _prompt_optional("Description (optional): ")

    prompt: Optional[str] = None
    if args.prompt is not None:
        prompt = args.prompt.strip() or None
    elif args.prompt_file:
        prompt = args.prompt_file.read_text(encoding="utf-8").strip() or None
    elif _is_interactive():
        prompt = _prompt_multiline_required(
            "Prompt template (end with empty line):",
            hint="Template syntax: {{args}} and !{...}.",
        )

    if not prompt:
        raise SystemExit(
            "prompt is required (pass --prompt/--prompt-file or input interactively)"
        )

    cmd = CommandConfig(name=name, description=description, prompt=prompt)
    path = save_command(cmd)
    success(f"Saved: {path}")


def _read_stdin() -> str:
    if sys.stdin.isatty():
        return ""
    return sys.stdin.read()


def handle_command_render(args: argparse.Namespace) -> None:
    name = _require_name(args.name)
    cmd = load_command(name)
    args_text = " ".join(args.args or []).strip()
    _ = _read_stdin()  # stdin is currently unused by spec, but may be used by shell.
    rendered = render_template(
        cmd.prompt or "",
        RenderContext(
            args_text=args_text,
            assume_yes=bool(args.yes),
            interactive=sys.stdin.isatty(),
        ),
    )
    print(rendered)


def handle_command_run(args: argparse.Namespace) -> None:
    lang = resolve_lang(getattr(args, "lang", None))
    api_key = get_api_key(getattr(args, "api_key", None))
    if not api_key:
        raise SystemExit(t("chat.err.missing_api_key", lang))

    base_url = resolve_base_url(getattr(args, "base_url", None))
    model = resolve_model(getattr(args, "model", None))
    if not model:
        raise SystemExit(t("chat.err.missing_model", lang))

    system_prompt = resolve_system_prompt(None)
    temperature = None
    top_p = None
    max_tokens = None
    presence_penalty = None
    frequency_penalty = None
    if getattr(args, "bot", None):
        bot = load_bot(args.bot)
        if bot.system_prompt:
            system_prompt = bot.system_prompt
        temperature = bot.temperature
        top_p = bot.top_p
        max_tokens = bot.max_tokens
        presence_penalty = bot.presence_penalty
        frequency_penalty = bot.frequency_penalty

    cmd = load_command(_require_name(args.name))
    args_text = " ".join(args.args or []).strip()
    _ = _read_stdin()  # allow shell commands to read stdin if needed
    prompt = render_template(
        cmd.prompt or "",
        RenderContext(
            args_text=args_text,
            assume_yes=bool(getattr(args, "yes", False)),
            interactive=sys.stdin.isatty(),
        ),
    ).strip()
    if not prompt:
        raise SystemExit("Command produced empty prompt.")

    messages: list[models.MessageTypedDict] = []
    if system_prompt:
        messages.append(
            cast(models.MessageTypedDict, {"role": "system", "content": system_prompt})
        )
    messages.append(cast(models.MessageTypedDict, {"role": "user", "content": prompt}))

    with R9S(api_key=api_key, server_url=base_url) as r9s:
        if getattr(args, "no_stream", False):
            spinner = Spinner("")
            if sys.stdout.isatty():
                spinner.start()
            try:
                res = r9s.chat.create(
                    model=model,
                    messages=messages,
                    stream=False,
                    temperature=temperature,
                    top_p=top_p,
                    max_tokens=max_tokens,
                    presence_penalty=presence_penalty,
                    frequency_penalty=frequency_penalty,
                )
                text = ""
                if res.choices and res.choices[0].message:
                    text = _content_to_text(res.choices[0].message.content)
            finally:
                spinner.stop_and_clear()
            print(text)
            return

        spinner = Spinner("")
        if sys.stdout.isatty():
            spinner.start()
        stream = r9s.chat.create(
            model=model,
            messages=messages,
            stream=True,
            temperature=temperature,
            top_p=top_p,
            max_tokens=max_tokens,
            presence_penalty=presence_penalty,
            frequency_penalty=frequency_penalty,
        )
        try:
            parts: list[str] = []
            for event in stream:
                if not event.choices:
                    continue
                delta = event.choices[0].delta
                if delta.content:
                    spinner.stop_and_clear()
                    parts.append(delta.content)
                    print(delta.content, end="", flush=True)
        finally:
            spinner.stop_and_clear()
        print()


def _content_to_text(content: Any) -> str:
    if content is None:
        return ""
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts: list[str] = []
        for item in content:
            if isinstance(item, dict):
                if item.get("type") == "text" and isinstance(item.get("text"), str):
                    parts.append(item["text"])
            else:
                item_type = getattr(item, "type", None)
                item_text = getattr(item, "text", None)
                if item_type == "text" and isinstance(item_text, str):
                    parts.append(item_text)
        if parts:
            return "".join(parts)
    try:
        return json.dumps(content, ensure_ascii=False)
    except Exception:
        return str(content)
