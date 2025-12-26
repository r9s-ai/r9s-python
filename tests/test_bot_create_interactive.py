from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pytest

from r9s.cli_tools.bot_cli import handle_bot_create
from r9s.cli_tools.bots import load_bot


def test_bot_create_prompts_for_system_prompt_when_missing(
    temp_home: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(sys.stdin, "isatty", lambda: True)

    inputs = iter(["You are a helper.", "", ""])  # multi-line ends on empty line
    monkeypatch.setattr(
        "r9s.cli_tools.bot_cli.prompt_text", lambda *_, **__: next(inputs)
    )

    args = argparse.Namespace(
        name="demo",
        description=None,
        system_prompt=None,
        temperature=None,
        top_p=None,
        max_tokens=None,
        presence_penalty=None,
        frequency_penalty=None,
    )

    handle_bot_create(args)
    bot = load_bot("demo")
    assert bot.system_prompt == "You are a helper."
