from __future__ import annotations

import json
from pathlib import Path

from r9s.cli_tools.tools.claude_code import ClaudeCodeIntegration


def test_claude_run_preflight_warns_on_env_conflict(
    temp_home: Path,  # noqa: ARG001
) -> None:
    tool = ClaudeCodeIntegration()
    tool._settings_path.parent.mkdir(parents=True, exist_ok=True)  # type: ignore[attr-defined]
    tool._settings_path.write_text(  # type: ignore[attr-defined]
        json.dumps(
            {
                "env": {
                    "ANTHROPIC_BASE_URL": "https://example.com",
                    "OTHER": "x",
                }
            }
        ),
        encoding="utf-8",
    )

    msg = tool.run_preflight(
        injected_env={"ANTHROPIC_BASE_URL": "https://r9s.ai", "ANTHROPIC_MODEL": "m"}
    )
    assert msg is not None
    assert "ANTHROPIC_BASE_URL" in msg


def test_claude_run_preflight_no_warning_when_no_env_conflict(
    temp_home: Path,  # noqa: ARG001
) -> None:
    tool = ClaudeCodeIntegration()
    tool._settings_path.parent.mkdir(parents=True, exist_ok=True)  # type: ignore[attr-defined]
    tool._settings_path.write_text(  # type: ignore[attr-defined]
        json.dumps({"env": {"OTHER": "x"}}),
        encoding="utf-8",
    )

    assert (
        tool.run_preflight(injected_env={"ANTHROPIC_MODEL": "m"})
        is None
    )
