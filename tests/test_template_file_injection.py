from __future__ import annotations

from pathlib import Path

import pytest

from r9s.cli_tools.template_renderer import RenderContext, render_template


def test_template_file_injection_reads_file(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    p = tmp_path / "doc.txt"
    p.write_text("hello\nworld\n", encoding="utf-8")
    monkeypatch.chdir(tmp_path)

    out = render_template(
        "X @{doc.txt} Y",
        RenderContext(args_text="", assume_yes=True, interactive=False),
    )
    assert out == "X hello\nworld\n Y"


def test_template_file_injection_does_not_execute_shell_from_file_content(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    p = tmp_path / "doc.txt"
    p.write_text("!{echo should_not_run}\n", encoding="utf-8")
    monkeypatch.chdir(tmp_path)

    monkeypatch.setattr(
        "r9s.cli_tools.template_renderer.subprocess.run",
        lambda *_, **__: (_ for _ in ()).throw(AssertionError("shell executed")),
    )

    out = render_template(
        "Injected: @{doc.txt}",
        RenderContext(args_text="", assume_yes=True, interactive=False),
    )
    assert "!{echo should_not_run}" in out


def test_template_file_injection_enforces_max_bytes_env(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    p = tmp_path / "big.txt"
    p.write_bytes(b"a" * 10)
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("R9S_FILE_INJECT_MAX_BYTES", "5")

    with pytest.raises(RuntimeError, match="File too large to inject"):
        render_template(
            "@{big.txt}",
            RenderContext(args_text="", assume_yes=True, interactive=False),
        )

