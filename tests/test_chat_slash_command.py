from __future__ import annotations

import sys
from dataclasses import dataclass
from typing import Any, Optional

import pytest

from r9s.cli_tools.chat_cli import handle_chat
from r9s.cli_tools.commands import CommandConfig


@dataclass
class _Delta:
    content: Optional[str] = None


@dataclass
class _Choice:
    delta: _Delta
    message: Any = None


@dataclass
class _Event:
    choices: list[_Choice]


class _ChatStub:
    def __init__(self) -> None:
        self.calls: list[dict[str, Any]] = []

    def create(self, **kwargs: Any) -> Any:
        self.calls.append(kwargs)

        class _Msg:
            content = "ok"

        class _Resp:
            choices = [type("C", (), {"message": _Msg()})()]

        return _Resp()


class _R9SStub:
    def __init__(self, *_, **__) -> None:
        self.chat = _ChatStub()

    def __enter__(self) -> "_R9SStub":
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        return None


def test_chat_slash_command_executes_command(monkeypatch: pytest.MonkeyPatch) -> None:
    # Force interactive mode
    monkeypatch.setattr(sys.stdin, "isatty", lambda: True)
    monkeypatch.setattr(sys.stdout, "isatty", lambda: True)

    # Command registry
    monkeypatch.setattr("r9s.cli_tools.chat_cli.list_commands", lambda: ["summarize"])
    monkeypatch.setattr(
        "r9s.cli_tools.chat_cli.load_command",
        lambda name: CommandConfig(name=name, prompt="Say {{args}}"),
    )

    # Provide inputs: slash command then exit
    inputs = iter(["/summarize hello", "/exit"])
    monkeypatch.setattr(
        "r9s.cli_tools.chat_cli.prompt_text", lambda *_, **__: next(inputs)
    )

    stub = _R9SStub()
    monkeypatch.setattr("r9s.cli_tools.chat_cli.R9S", lambda **_: stub)
    monkeypatch.setenv("R9S_MODEL", "m")

    args = type(
        "Args",
        (),
        {
            "lang": None,
            "api_key": "k",
            "base_url": None,
            "model": None,
            "system_prompt": None,
            "history_file": None,
            "no_history": True,
            "ext": [],
            "no_stream": True,
            "yes": True,
            "bot": None,
        },
    )()

    handle_chat(args)
    assert stub.chat.calls
    call = stub.chat.calls[-1]
    assert call["stream"] is False
    assert call["messages"][-1]["content"] == "Say hello"
