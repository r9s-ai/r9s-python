from __future__ import annotations

import argparse
import base64
import json
import sys
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, List, Optional

from r9s import models
from r9s.models.message import Role
from r9s.cli_tools.bots import BotConfig, load_bot
from r9s.cli_tools.commands import list_commands, load_command
from r9s.cli_tools.template_renderer import RenderContext, render_template
from r9s.cli_tools.chat_extensions import (
    ChatContext,
    load_extensions,
    parse_extension_specs,
    run_after_response_extensions,
    run_before_request_extensions,
    run_stream_delta_extensions,
    run_user_input_extensions,
)
from r9s.cli_tools.config import (
    get_api_key,
    resolve_base_url,
    resolve_model,
    resolve_system_prompt,
)
from r9s.cli_tools.i18n import resolve_lang, t
from r9s.cli_tools.ui.terminal import FG_CYAN, error, header, info, prompt_text
from r9s.cli_tools.ui.spinner import Spinner
from r9s.sdk import R9S


@dataclass
class SessionMeta:
    session_id: str
    created_at: str
    updated_at: str
    base_url: str
    model: str
    system_prompt: Optional[str] = None


@dataclass
class SessionRecord:
    meta: SessionMeta
    messages: List[models.MessageTypedDict]


def _require_api_key(args_api_key: Optional[str], lang: str) -> str:
    key = get_api_key(args_api_key)
    if not key:
        raise SystemExit(t("chat.err.missing_api_key", lang))
    return key


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _history_root() -> Path:
    return Path.home() / ".r9s" / "chat"


def _default_session_path() -> Path:
    root = _history_root()
    root.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    sid = uuid.uuid4().hex[:8]
    return root / f"{stamp}_{sid}.json"


def _coerce_messages(value: Any) -> List[models.MessageTypedDict]:
    if not isinstance(value, list):
        raise TypeError("history is not a JSON array")
    out: List[models.MessageTypedDict] = []
    for item in value:
        if not isinstance(item, dict):
            continue
        role = item.get("role")
        content = item.get("content")
        if isinstance(role, str) and role in ("system", "user", "assistant", "tool"):
            role_typed: Role = role
            if isinstance(content, str):
                out.append({"role": role_typed, "content": content})
                continue
            if isinstance(content, list) and all(isinstance(x, dict) for x in content):
                out.append({"role": role_typed, "content": content})
    return out


def _load_history(path: str) -> SessionRecord:
    try:
        raw = Path(path).read_text(encoding="utf-8")
    except FileNotFoundError:
        raise
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise ValueError(str(exc)) from exc
    # Backward compatible:
    # - list[...] => messages only
    # - {"meta": {...}, "messages": [...]} => full record
    if isinstance(data, list):
        now = _utc_now_iso()
        meta = SessionMeta(
            session_id=Path(path).stem,
            created_at=now,
            updated_at=now,
            base_url="",
            model="",
            system_prompt=None,
        )
        return SessionRecord(meta=meta, messages=_coerce_messages(data))
    if isinstance(data, dict):
        messages = _coerce_messages(data.get("messages", []))
        meta_raw = data.get("meta", {}) if isinstance(data.get("meta"), dict) else {}
        now = _utc_now_iso()
        meta = SessionMeta(
            session_id=str(meta_raw.get("session_id") or Path(path).stem),
            created_at=str(meta_raw.get("created_at") or now),
            updated_at=str(meta_raw.get("updated_at") or now),
            base_url=str(meta_raw.get("base_url") or ""),
            model=str(meta_raw.get("model") or ""),
            system_prompt=(
                str(meta_raw.get("system_prompt"))
                if meta_raw.get("system_prompt")
                else None
            ),
        )
        return SessionRecord(meta=meta, messages=messages)
    raise TypeError("history is not a JSON array")


def _save_history(path: str, record: SessionRecord) -> None:
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "meta": {
            "session_id": record.meta.session_id,
            "created_at": record.meta.created_at,
            "updated_at": record.meta.updated_at,
            "base_url": record.meta.base_url,
            "model": record.meta.model,
            "system_prompt": record.meta.system_prompt,
        },
        "messages": record.messages,
    }
    Path(path).write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )


def _build_messages(
    system_prompt: Optional[str],
    history: List[models.MessageTypedDict],
) -> List[models.MessageTypedDict]:
    messages: List[models.MessageTypedDict] = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    messages.extend(history)
    return messages


def _print_help_lang(lang: str) -> None:
    info(t("chat.commands.title", lang))
    print(t("chat.commands.exit", lang))
    print(t("chat.commands.clear", lang))
    print(t("chat.commands.help", lang))


def _is_piped_stdin() -> bool:
    return not sys.stdin.isatty()


def _read_piped_input_bytes() -> bytes:
    try:
        return sys.stdin.buffer.read()
    except Exception:
        return sys.stdin.read().encode("utf-8", errors="replace")


def _is_probably_text(data: bytes) -> bool:
    if not data:
        return True
    if b"\x00" in data:
        return False
    try:
        data.decode("utf-8")
        return True
    except UnicodeDecodeError:
        return False


def _detect_image_mime(data: bytes) -> Optional[str]:
    if data.startswith(b"\x89PNG\r\n\x1a\n"):
        return "image/png"
    if data.startswith(b"\xff\xd8\xff"):
        return "image/jpeg"
    if data.startswith(b"GIF87a") or data.startswith(b"GIF89a"):
        return "image/gif"
    if data.startswith(b"RIFF") and data[8:12] == b"WEBP":
        return "image/webp"
    return None


def _build_user_message_from_piped_stdin(
    raw: bytes, *, lang: str, exts: List[Any], ctx: ChatContext
) -> Optional[models.MessageTypedDict]:
    data = raw.strip()
    if not data:
        return None

    mime = _detect_image_mime(data)
    if mime:
        if len(data) > 10 * 1024 * 1024:
            raise SystemExit("Image from stdin is too large (max 10MB).")
        instruction = "Describe this image."
        instruction = run_user_input_extensions(exts, instruction, ctx)
        b64 = base64.b64encode(data).decode("ascii")
        url = f"data:{mime};base64,{b64}"
        return {
            "role": "user",
            "content": [
                {"type": "text", "text": instruction},
                {"type": "image_url", "image_url": {"url": url, "detail": "auto"}},
            ],
        }

    if _is_probably_text(data):
        text = data.decode("utf-8", errors="replace").strip()
        if not text:
            return None
        text = run_user_input_extensions(exts, text, ctx)
        return {"role": "user", "content": text}

    raise SystemExit(
        "stdin does not look like UTF-8 text or a supported image (png/jpeg/gif/webp)."
    )


def _stream_chat(
    r9s: R9S,
    model: str,
    messages: List[models.MessageTypedDict],
    ctx: ChatContext,
    exts: List[Any],
    *,
    prefix: Optional[str] = None,
    temperature: Optional[float] = None,
    top_p: Optional[float] = None,
    max_tokens: Optional[int] = None,
    presence_penalty: Optional[float] = None,
    frequency_penalty: Optional[float] = None,
) -> str:
    spinner = Spinner(prefix or "")
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
    assistant_parts: List[str] = []
    for event in stream:
        if not event.choices:
            continue
        delta = event.choices[0].delta
        if delta.content:
            spinner.stop_and_clear()
            piece = run_stream_delta_extensions(exts, delta.content, ctx)
            assistant_parts.append(piece)
            if prefix and not spinner.prefix_printed:
                spinner.print_prefix()
            print(piece, end="", flush=True)
    spinner.stop_and_clear()
    if prefix and not spinner.prefix_printed:
        spinner.print_prefix()
    print()
    assistant_text = "".join(assistant_parts)
    return run_after_response_extensions(exts, assistant_text, ctx)


def _non_stream_chat(
    r9s: R9S,
    model: str,
    messages: List[models.MessageTypedDict],
    ctx: ChatContext,
    exts: List[Any],
    *,
    prefix: Optional[str] = None,
    temperature: Optional[float] = None,
    top_p: Optional[float] = None,
    max_tokens: Optional[int] = None,
    presence_penalty: Optional[float] = None,
    frequency_penalty: Optional[float] = None,
) -> str:
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
    text = run_after_response_extensions(exts, text, ctx)
    if prefix:
        print(prefix, end="", flush=True)
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
    api_key = _require_api_key(args.api_key, lang)

    piped_stdin_bytes: Optional[bytes] = None
    if _is_piped_stdin():
        piped_stdin_bytes = _read_piped_input_bytes()

    bot_or_action = getattr(args, "bot", None)
    if bot_or_action == "resume":
        if not sys.stdin.isatty():
            raise SystemExit(t("chat.err.resume_requires_tty", lang))
        selected = _resume_select_session(lang)
        if selected is None:
            raise SystemExit(t("chat.resume.none", lang, dir=str(_history_root())))
        args.history_file = str(selected)
        bot_or_action = None

    bot: Optional[BotConfig] = None
    if bot_or_action:
        try:
            bot = load_bot(bot_or_action)
        except FileNotFoundError as exc:
            raise SystemExit(f"Bot not found: {bot_or_action}") from exc
        except Exception as exc:
            raise SystemExit(f"Failed to load bot: {bot_or_action} ({exc})") from exc

        if getattr(args, "system_prompt", None) is None and bot.system_prompt:
            args.system_prompt = bot.system_prompt

    bot_generation = {
        "temperature": bot.temperature if bot else None,
        "top_p": bot.top_p if bot else None,
        "max_tokens": bot.max_tokens if bot else None,
        "presence_penalty": bot.presence_penalty if bot else None,
        "frequency_penalty": bot.frequency_penalty if bot else None,
    }

    base_url = resolve_base_url(args.base_url)
    model = resolve_model(args.model)
    system_prompt = resolve_system_prompt(args.system_prompt)

    history_path: Optional[str]
    if args.no_history:
        history_path = None
    else:
        history_path = args.history_file or str(_default_session_path())

    record: Optional[SessionRecord] = None
    if history_path and Path(history_path).exists():
        try:
            record = _load_history(history_path)
        except ValueError as exc:
            raise SystemExit(
                t("chat.err.history_not_json", lang, path=history_path, err=str(exc))
            ) from exc
        except TypeError as exc:
            raise SystemExit(
                t("chat.err.history_not_array", lang, path=history_path)
            ) from exc

    if record is None:
        now = _utc_now_iso()
        record = SessionRecord(
            meta=SessionMeta(
                session_id=Path(history_path).stem
                if history_path
                else uuid.uuid4().hex,
                created_at=now,
                updated_at=now,
                base_url=base_url,
                model=model,
                system_prompt=system_prompt,
            ),
            messages=[],
        )
    else:
        # Resume can derive base_url/model/system_prompt from saved session when not specified.
        if not base_url and record.meta.base_url:
            base_url = record.meta.base_url
        if not model and record.meta.model:
            model = record.meta.model
        if system_prompt is None and record.meta.system_prompt is not None:
            system_prompt = record.meta.system_prompt

        # Fill meta if still missing (backward compatible)
        if not record.meta.base_url and base_url:
            record.meta.base_url = base_url
        if not record.meta.model and model:
            record.meta.model = model
        if record.meta.system_prompt is None:
            record.meta.system_prompt = system_prompt
        record.meta.updated_at = _utc_now_iso()

    if not model:
        raise SystemExit(t("chat.err.missing_model", lang))

    ctx = ChatContext(
        base_url=base_url,
        model=model,
        system_prompt=system_prompt,
        history_file=history_path,
        history=record.messages,
    )

    ext_specs = parse_extension_specs(args.ext)
    if ext_specs:
        try:
            exts = load_extensions(ext_specs)
        except ImportError as exc:
            message = str(exc)
            if message.startswith("Failed to load extension file:"):
                raise SystemExit(
                    t(
                        "chat.err.ext_load_file",
                        lang,
                        path=message.split(":", 1)[1].strip(),
                    )
                ) from exc
            if "Extension must provide one of" in message:
                raise SystemExit(t("chat.err.ext_contract", lang)) from exc
            raise
    else:
        exts = []

    command_names = set(list_commands()) if sys.stdin.isatty() else set()

    with R9S(api_key=api_key, server_url=base_url) as r9s:
        if piped_stdin_bytes is not None:
            user_msg = _build_user_message_from_piped_stdin(
                piped_stdin_bytes, lang=lang, exts=exts, ctx=ctx
            )
            if user_msg is None:
                return
            ctx.history.append(user_msg)
            messages = run_before_request_extensions(
                exts, _build_messages(system_prompt, ctx.history), ctx
            )
            assistant_text = (
                _non_stream_chat(
                    r9s,
                    model,
                    messages,
                    ctx,
                    exts,
                    **bot_generation,
                )
                if args.no_stream
                else _stream_chat(
                    r9s,
                    model,
                    messages,
                    ctx,
                    exts,
                    **bot_generation,
                )
            )
            ctx.history.append({"role": "assistant", "content": assistant_text})
            if history_path:
                record.meta.updated_at = _utc_now_iso()
                record.messages = ctx.history
                _save_history(history_path, record)
            return

        header(t("chat.title", lang))
        info(f"{t('chat.base_url', lang)}: {base_url}")
        info(f"{t('chat.model', lang)}: {model}")
        bot_display = bot_or_action or "(none)"
        info(f"bot: {bot_display}")
        if command_names:
            info("slash commands: " + ", ".join(f"/{n}" for n in sorted(command_names)))
        if exts:
            info(
                f"{t('chat.extensions', lang)}: "
                + ", ".join(getattr(e, "name", e.__class__.__name__) for e in exts)
            )
        _print_help_lang(lang)
        print()

        while True:
            try:
                user_text = prompt_text(
                    _style_prompt(t("chat.prompt.user", lang)), color=FG_CYAN
                )
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
                parts = cmd[1:].split(" ", 1)
                command_name = parts[0]
                args_text = parts[1] if len(parts) > 1 else ""
                if command_name in command_names:
                    try:
                        cfg = load_command(command_name)
                        rendered = render_template(
                            cfg.prompt or "",
                            RenderContext(
                                args_text=args_text.strip(),
                                assume_yes=bool(getattr(args, "yes", False)),
                                interactive=True,
                            ),
                        ).strip()
                    except Exception as exc:
                        error(f"Command failed: /{command_name} ({exc})")
                        continue
                    if not rendered:
                        error("Command produced empty prompt.")
                        continue
                    user_text = rendered
                else:
                    error(t("chat.err.unknown_command", lang, cmd=cmd))
                    continue

            user_text = run_user_input_extensions(exts, user_text, ctx)
            ctx.history.append({"role": "user", "content": user_text})

            messages = _build_messages(system_prompt, ctx.history)
            messages = run_before_request_extensions(exts, messages, ctx)

            assistant_text = (
                _non_stream_chat(
                    r9s,
                    model,
                    messages,
                    ctx,
                    exts,
                    prefix=_style_prompt(t("chat.prompt.assistant", lang)),
                    **bot_generation,
                )
                if args.no_stream
                else _stream_chat(
                    r9s,
                    model,
                    messages,
                    ctx,
                    exts,
                    prefix=_style_prompt(t("chat.prompt.assistant", lang)),
                    **bot_generation,
                )
            )
            ctx.history.append({"role": "assistant", "content": assistant_text})

            if history_path:
                record.meta.updated_at = _utc_now_iso()
                record.messages = ctx.history
                _save_history(history_path, record)


def _style_prompt(text: str) -> str:
    # 避免在这里引入更多样式依赖：prompt_text 已支持颜色，但我们希望保持提示一致性
    return text


def _resume_select_session(lang: str) -> Optional[Path]:
    root = _history_root()
    if not root.exists():
        return None
    sessions = _list_sessions(root)
    if not sessions:
        return None
    info(f"Sessions in: {root}")
    for idx, s in enumerate(sessions, start=1):
        print(f"{idx}) {s.display}")
    while True:
        selection = prompt_text(t("chat.resume.select", lang))
        if not selection.isdigit():
            error(t("chat.resume.invalid", lang))
            continue
        num = int(selection)
        if 1 <= num <= len(sessions):
            return sessions[num - 1].path
        error(t("chat.resume.invalid", lang))


@dataclass
class SessionInfo:
    path: Path
    updated_at: str
    display: str


def _list_sessions(root: Path) -> List[SessionInfo]:
    out: List[SessionInfo] = []
    for path in sorted(
        root.glob("*.json"), key=lambda p: p.stat().st_mtime, reverse=True
    ):
        try:
            rec = _load_history(str(path))
        except Exception:
            continue
        updated = rec.meta.updated_at or ""
        base = rec.meta.base_url or "?"
        model = rec.meta.model or "?"
        preview = ""
        for msg in reversed(rec.messages):
            content = msg.get("content")
            if msg.get("role") == "user" and isinstance(content, str):
                preview = content.replace("\n", " ")
                break
        if preview:
            preview = (preview[:60] + "…") if len(preview) > 60 else preview
        display = f"{path.name}  [{updated}]  {model}  {base}"
        if preview:
            display += f"  - {preview}"
        out.append(SessionInfo(path=path, updated_at=updated, display=display))
    return out
