from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, List

from r9s.cli_tools.ui.terminal import (
    BOLD,
    FG_ACCENT,
    FG_CMD,
    FG_MUTED,
    FG_NOTE,
    FG_TITLE,
    _style,
)


@dataclass(frozen=True)
class ExampleBlock:
    title: str
    notes: List[str]
    commands: List[str]


def _parse_example_block(raw: str) -> ExampleBlock:
    lines = [ln.rstrip() for ln in raw.splitlines()]
    title: str | None = None
    notes: List[str] = []
    commands: List[str] = []
    for ln in lines:
        s = ln.strip()
        if not s:
            continue
        if s.startswith("#"):
            text = s.lstrip("#").strip()
            if not text:
                continue
            if title is None:
                title = text
            else:
                notes.append(text)
        else:
            commands.append(s)
    return ExampleBlock(title=title or "Example", notes=notes, commands=commands)


def print_home(
    *,
    name: str,
    description: str,
    examples_title: str,
    examples: Iterable[str],
    footer: str,
) -> None:
    print(_style(name, BOLD, FG_TITLE))
    if description:
        print(_style(description, FG_MUTED))
    print()

    if examples_title:
        print(_style(examples_title, BOLD, FG_TITLE))

    for raw in examples:
        block = _parse_example_block(raw)
        if not block.commands:
            continue
        print(_style(f"- {block.title}", FG_ACCENT))
        for note in block.notes:
            print(_style(f"  {note}", FG_NOTE))
        for cmd in block.commands:
            print(_style(f"  {cmd}", FG_CMD))
        print()

    if footer:
        print(_style(footer, FG_MUTED))
