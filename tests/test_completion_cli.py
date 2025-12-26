from __future__ import annotations

from r9s.cli_tools.completion_cli import compute_completions


def test_completion_top_level_commands() -> None:
    out = compute_completions("bash", 0, [""])
    assert "chat" in out
    assert "completion" in out
    assert "command" in out


def test_completion_run_apps_includes_cc() -> None:
    out = compute_completions("bash", 1, ["run", ""])
    assert "cc" in out
    assert "claude-code" in out
