from __future__ import annotations

from pathlib import Path

from r9s.cli_tools.chat_cli import (
    SessionMeta,
    SessionRecord,
    _history_root,
    _list_sessions,
    _save_history,
)


def test_resume_list_display_is_time_and_prompt_only(temp_home: Path) -> None:  # noqa: ARG001
    root = _history_root()
    path = root / "demo.json"
    record = SessionRecord(
        meta=SessionMeta(
            session_id="demo",
            created_at="2025-12-27T07:28:52+00:00",
            updated_at="2025-12-27T07:28:52+00:00",
            base_url="https://api.example.com/v1",
            model="gpt-5-mini",
            system_prompt=None,
        ),
        messages=[
            {"role": "user", "content": "generate\\ndiff\\nhello"},
        ],
    )
    _save_history(str(path), record)

    sessions = _list_sessions(root)
    assert sessions
    display = sessions[0].display
    assert "2025-" in display
    assert "generate" in display
    assert "\\n" not in display
    assert "http" not in display
    assert "gpt" not in display
    assert ".json" not in display
