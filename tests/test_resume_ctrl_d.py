from __future__ import annotations

from pathlib import Path

import pytest

from r9s.cli_tools.chat_cli import SessionMeta, SessionRecord, _history_root, _save_history


def test_resume_ctrl_d_exits_cleanly(temp_home: Path, monkeypatch: pytest.MonkeyPatch) -> None:  # noqa: ARG001
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
        messages=[{"role": "user", "content": "hello"}],
    )
    _save_history(str(path), record)

    monkeypatch.setattr("r9s.cli_tools.chat_cli.prompt_text", lambda *_, **__: (_ for _ in ()).throw(EOFError()))

    # Import here to avoid circulars in test collection.
    from r9s.cli_tools.chat_cli import _resume_select_session

    with pytest.raises(SystemExit) as exc:
        _resume_select_session("en")
    assert exc.value.code == 0

