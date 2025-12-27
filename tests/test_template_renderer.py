from __future__ import annotations

import sys

import pytest

from r9s.cli_tools.template_renderer import RenderContext, render_template


def test_render_template_replaces_args() -> None:
    out = render_template(
        "Hello {{args}}!",
        RenderContext(args_text="world", assume_yes=True, interactive=False),
    )
    assert out == "Hello world!"


def test_shell_requires_yes_in_non_interactive(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(sys.stdin, "isatty", lambda: False)
    with pytest.raises(RuntimeError, match="requires confirmation"):
        render_template(
            "X=!{echo hi}",
            RenderContext(args_text="", assume_yes=False, interactive=False),
        )


def test_shell_runs_with_yes_in_non_interactive(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(sys.stdin, "isatty", lambda: False)
    out = render_template(
        "X=!{echo hi}", RenderContext(args_text="", assume_yes=True, interactive=False)
    )
    assert out.strip() == "X=hi"
