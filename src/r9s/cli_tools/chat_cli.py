from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any, List, Optional

from r9s import models
from r9s.models.message import Role
from r9s.cli_tools.chat_extensions import (
    ChatContext,
    load_extensions,
    parse_extension_specs,
    run_after_response_extensions,
    run_before_request_extensions,
    run_stream_delta_extensions,
    run_user_input_extensions,
)
from r9s.cli_tools.i18n import resolve_lang, t
from r9s.cli_tools.terminal import FG_CYAN, error, header, info, prompt_text
from r9s.sdk import R9S


def _resolve_api_key(args_api_key: Optional[str]) -> str:
    return (
        os.getenv("R9S_API_KEY")
        or args_api_key
        or ""
    )


def _resolve_base_url(args_base_url: Optional[str]) -> str:
    return (
        args_base_url
        or os.getenv("R9S_BASE_URL")
        or "https://api.r9s.ai"
    )


def _resolve_model(args_model: Optional[str]) -> str:
    return (args_model or os.getenv("R9S_MODEL") or "").strip()


def _resolve_system_prompt(args_system_prompt: Optional[str], args_file: Optional[str]) -> Optional[str]:
    if args_system_prompt:
        return args_system_prompt
    if args_file:
        return Path(args_file).read_text(encoding="utf-8").strip() or None
    env = os.getenv("R9S_SYSTEM_PROMPT")
    return env.strip() if env else None


def _load_history(path: str) -> List[models.MessageTypedDict]:
    try:
        raw = Path(path).read_text(encoding="utf-8")
    except FileNotFoundError:
        return []
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise ValueError(str(exc)) from exc
    if not isinstance(data, list):
        raise TypeError("history is not a JSON array")
    out: List[models.MessageTypedDict] = []
    for item in data:
        if not isinstance(item, dict):
            continue
        role = item.get("role")
        content = item.get("content")
        if isinstance(role, str) and role in ("system", "user", "assistant", "tool") and isinstance(content, str):
            role_typed: Role = role
            out.append({"role": role_typed, "content": content})
    return out


def _save_history(path: str, history: List[models.MessageTypedDict]) -> None:
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text(json.dumps(history, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _build_messages(
    system_prompt: Optional[str],
    history: List[models.MessageTypedDict],
) -> List[models.MessageTypedDict]:
    messages: List[models.MessageTypedDict] = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    messages.extend(history)
    return messages


def _print_help() -> None:
    # Deprecated: kept for compatibility, but prefer _print_help_lang.
    info("Commands:")
    print("  /exit   Exit")
    print("  /clear  Clear session history (does not delete history-file)")
    print("  /help   Show help")
    print("  other /xxx  Handled by extensions (--ext)")


def _print_help_lang(lang: str) -> None:
    info(t("chat.commands.title", lang))
    print(t("chat.commands.exit", lang))
    print(t("chat.commands.clear", lang))
    print(t("chat.commands.help", lang))


def _is_piped_stdin() -> bool:
    return not sys.stdin.isatty()


def _read_piped_input() -> str:
    return sys.stdin.read()


def _stream_chat(
    r9s: R9S,
    model: str,
    messages: List[models.MessageTypedDict],
    ctx: ChatContext,
    exts: List[Any],
) -> str:
    stream = r9s.chat.create(model=model, messages=messages, stream=True)
    assistant_parts: List[str] = []
    print("", end="", flush=True)
    for event in stream:
        if not event.choices:
            continue
        delta = event.choices[0].delta
        if delta.content:
            piece = run_stream_delta_extensions(exts, delta.content, ctx)
            assistant_parts.append(piece)
            print(piece, end="", flush=True)
    print()
    assistant_text = "".join(assistant_parts)
    return run_after_response_extensions(exts, assistant_text, ctx)


def _non_stream_chat(
    r9s: R9S,
    model: str,
    messages: List[models.MessageTypedDict],
    ctx: ChatContext,
    exts: List[Any],
) -> str:
    res = r9s.chat.create(model=model, messages=messages, stream=False)
    text = ""
    if res.choices and res.choices[0].message:
        text = _content_to_text(res.choices[0].message.content)
    text = run_after_response_extensions(exts, text, ctx)
    print(text)
    return text


def _content_to_text(content: Any) -> str:
    if content is None:
        return ""
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts: List[str] = []
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


def handle_chat(args: argparse.Namespace) -> None:
    lang = resolve_lang(getattr(args, "lang", None))
    api_key = _resolve_api_key(args.api_key)
    if not api_key:
        raise SystemExit(t("chat.err.missing_api_key", lang))

    base_url = _resolve_base_url(args.base_url)
    model = _resolve_model(args.model)
    if not model:
        raise SystemExit(t("chat.err.missing_model", lang))

    system_prompt = _resolve_system_prompt(args.system_prompt, args.system_prompt_file)
    history: List[models.MessageTypedDict] = []
    if args.history_file:
        try:
            history = _load_history(args.history_file)
        except ValueError as exc:
            raise SystemExit(
                t("chat.err.history_not_json", lang, path=args.history_file, err=str(exc))
            ) from exc
        except TypeError as exc:
            raise SystemExit(t("chat.err.history_not_array", lang, path=args.history_file)) from exc

    ctx = ChatContext(
        base_url=base_url,
        model=model,
        system_prompt=system_prompt,
        history_file=args.history_file,
        history=history,
    )

    ext_specs = parse_extension_specs(args.ext)
    if ext_specs:
        try:
            exts = load_extensions(ext_specs)
        except ImportError as exc:
            message = str(exc)
            if message.startswith("Failed to load extension file:"):
                raise SystemExit(
                    t("chat.err.ext_load_file", lang, path=message.split(":", 1)[1].strip())
                ) from exc
            if "Extension must provide one of" in message:
                raise SystemExit(t("chat.err.ext_contract", lang)) from exc
            raise
    else:
        exts = []

    with R9S(api_key=api_key, server_url=base_url) as r9s:
        if _is_piped_stdin():
            user_text = _read_piped_input().strip()
            if not user_text:
                return
            user_text = run_user_input_extensions(exts, user_text, ctx)
            ctx.history.append({"role": "user", "content": user_text})
            messages = run_before_request_extensions(exts, _build_messages(system_prompt, ctx.history), ctx)
            assistant_text = (
                _non_stream_chat(r9s, model, messages, ctx, exts)
                if args.no_stream
                else _stream_chat(r9s, model, messages, ctx, exts)
            )
            ctx.history.append({"role": "assistant", "content": assistant_text})
            if args.history_file:
                _save_history(args.history_file, ctx.history)
            return

        header(t("chat.title", lang))
        info(f"{t('chat.base_url', lang)}: {base_url}")
        info(f"{t('chat.model', lang)}: {model}")
        if system_prompt:
            info(t("chat.system_prompt_set", lang))
        if exts:
            info(
                f"{t('chat.extensions', lang)}: "
                + ", ".join(getattr(e, "name", e.__class__.__name__) for e in exts)
            )
        _print_help_lang(lang)
        print()

        while True:
            try:
                user_text = prompt_text(_style_prompt(t("chat.prompt.user", lang)), color=FG_CYAN)
            except EOFError:
                print()
                return

            if not user_text:
                continue

            if user_text.startswith("/"):
                cmd = user_text.strip()
                if cmd == "/exit":
                    return
                if cmd == "/help":
                    _print_help_lang(lang)
                    continue
                if cmd == "/clear":
                    ctx.history.clear()
                    info(t("chat.msg.history_cleared", lang))
                    continue
                error(t("chat.err.unknown_command", lang, cmd=cmd))
                continue

            user_text = run_user_input_extensions(exts, user_text, ctx)
            ctx.history.append({"role": "user", "content": user_text})

            messages = _build_messages(system_prompt, ctx.history)
            messages = run_before_request_extensions(exts, messages, ctx)

            print(_style_prompt(t("chat.prompt.assistant", lang)), end="", flush=True)
            assistant_text = (
                _non_stream_chat(r9s, model, messages, ctx, exts)
                if args.no_stream
                else _stream_chat(r9s, model, messages, ctx, exts)
            )
            ctx.history.append({"role": "assistant", "content": assistant_text})

            if args.history_file:
                _save_history(args.history_file, ctx.history)


def _style_prompt(text: str) -> str:
    # 避免在这里引入更多样式依赖：prompt_text 已支持颜色，但我们希望保持提示一致性
    return text
