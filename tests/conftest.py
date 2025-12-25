from __future__ import annotations

import os
from pathlib import Path

import pytest


@pytest.fixture()
def temp_home(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Isolate Path.home() + ~/.r9s writes into a temp directory."""
    monkeypatch.setenv("HOME", str(tmp_path))
    # Some libs also read USERPROFILE on Windows; harmless on Linux.
    monkeypatch.setenv("USERPROFILE", str(tmp_path))
    # Ensure expanduser uses this HOME.
    os.environ["HOME"] = str(tmp_path)
    return tmp_path
