from __future__ import annotations

from pathlib import Path

import pytest

from r9s.skills.exceptions import SecurityError, SkillNotFoundError
from r9s.skills.local_store import (
    delete_skill,
    list_skills,
    load_skill,
    save_skill,
    skill_path,
)
from r9s.skills.models import ScriptPolicy


def _skill_content() -> str:
    return """---
name: code-review
description: Review code
---

# Code Review

Use this skill.
"""


def test_skill_store_crud(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("R9S_SKILLS_DIR", str(tmp_path))
    save_skill("code-review", _skill_content())

    skill_dir = skill_path("code-review")
    (skill_dir / "scripts").mkdir(parents=True)
    (skill_dir / "references").mkdir(parents=True)
    (skill_dir / "assets").mkdir(parents=True)
    (skill_dir / "scripts" / "lint.sh").write_text("echo ok", encoding="utf-8")
    (skill_dir / "references" / "readme.md").write_text("doc", encoding="utf-8")
    (skill_dir / "assets" / "logo.png").write_bytes(b"img")

    assert list_skills() == ["code-review"]

    skill = load_skill("code-review")
    assert skill.name == "code-review"
    assert "scripts/lint.sh" in skill.scripts
    assert "references/readme.md" in skill.references
    assert "assets/logo.png" in skill.assets

    delete_skill("code-review")
    assert not skill_dir.exists()


def test_load_skill_not_found(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("R9S_SKILLS_DIR", str(tmp_path))
    with pytest.raises(SkillNotFoundError, match="not-a-skill"):
        load_skill("not-a-skill")


def test_delete_skill_not_found(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("R9S_SKILLS_DIR", str(tmp_path))
    with pytest.raises(SkillNotFoundError, match="missing-skill"):
        delete_skill("missing-skill")


def test_load_skill_with_scripts_blocked(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("R9S_SKILLS_DIR", str(tmp_path))
    save_skill("script-skill", _skill_content().replace("code-review", "script-skill"))

    skill_dir = skill_path("script-skill")
    scripts_dir = skill_dir / "scripts"
    scripts_dir.mkdir()
    (scripts_dir / "run.sh").write_text("echo hi", encoding="utf-8")

    # Should fail with scripts blocked
    with pytest.raises(SecurityError, match="--allow-scripts"):
        load_skill("script-skill", policy=ScriptPolicy(allow_scripts=False))

    # Should pass with scripts allowed
    skill = load_skill("script-skill", policy=ScriptPolicy(allow_scripts=True))
    assert skill.name == "script-skill"
    assert "scripts/run.sh" in skill.scripts
