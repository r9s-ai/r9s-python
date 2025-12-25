from __future__ import annotations

import sys
from dataclasses import dataclass
from typing import Any, Iterator, Optional

import pytest

from r9s.cli_tools.command_cli import handle_command_run
from r9s.cli_tools.commands import CommandConfig, save_command


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
        if kwargs.get("stream") is False:
            # Minimal non-stream response shape used by command_cli
            class _Msg:
                content = "ok"

            class _Resp:
                choices = [type("C", (), {"message": _Msg()})()]

            return _Resp()

        def _gen() -> Iterator[_Event]:
            yield _Event(choices=[_Choice(delta=_Delta(content="ok"))])

        return _gen()


class _R9SStub:
    def __init__(self, *_, **__) -> None:
        self.chat = _ChatStub()

    def __enter__(self) -> "_R9SStub":
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        return None


def test_command_run_calls_chat_create(
    temp_home, monkeypatch: pytest.MonkeyPatch
) -> None:
    save_command(CommandConfig(name="summarize", prompt="Say {{args}}"))
    monkeypatch.setenv("R9S_API_KEY", "k")
    monkeypatch.setenv("R9S_MODEL", "m")
    monkeypatch.setattr(sys.stdin, "isatty", lambda: False)
    monkeypatch.setattr("r9s.cli_tools.command_cli._read_stdin", lambda: "")

    stub = _R9SStub()
    monkeypatch.setattr("r9s.cli_tools.command_cli.R9S", lambda **_: stub)

    args = type(
        "Args",
        (),
        {
            "name": "summarize",
            "args": ["hello"],
            "lang": None,
            "api_key": None,
            "base_url": None,
            "model": None,
            "no_stream": True,
            "yes": True,
            "bot": None,
        },
    )()

    handle_command_run(args)  # should not raise
    assert stub.chat.calls
    call = stub.chat.calls[-1]
    assert call["model"] == "m"
    assert call["stream"] is False
    assert call["messages"][-1]["content"] == "Say hello"
