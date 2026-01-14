from __future__ import annotations

from pathlib import Path

import pytest

from r9s.skills.exceptions import InvalidSkillError, SecurityError
from r9s.skills.models import ScriptPolicy
from r9s.skills.validator import ensure_within_root, validate_skill_directory, validate_skill_name


def test_validate_skill_name() -> None:
    assert validate_skill_name("code-review") == "code-review"
    with pytest.raises(InvalidSkillError):
        validate_skill_name("Code-Review")
    with pytest.raises(InvalidSkillError):
        validate_skill_name("code_review")
    with pytest.raises(InvalidSkillError):
        validate_skill_name("a" * 65)


def test_ensure_within_root(tmp_path: Path) -> None:
    root = tmp_path / "skills"
    root.mkdir()
    ok = root / "demo"
    ok.mkdir()
    ensure_within_root(root, ok)
    outside = root / ".." / "escape"
    with pytest.raises(SecurityError):
        ensure_within_root(root, outside)


def test_validate_skill_directory_blocks_scripts(tmp_path: Path) -> None:
    skill_dir = tmp_path / "my-skill"
    skill_dir.mkdir()
    manifest = skill_dir / "SKILL.md"
    manifest.write_text(
        """---
name: my-skill
description: A skill with scripts
---

Instructions here.
""",
        encoding="utf-8",
    )
    # Add a script
    scripts_dir = skill_dir / "scripts"
    scripts_dir.mkdir()
    (scripts_dir / "run.sh").write_text("#!/bin/bash\necho hello", encoding="utf-8")

    # Should fail without allow_scripts
    with pytest.raises(SecurityError, match="--allow-scripts"):
        validate_skill_directory(skill_dir, policy=ScriptPolicy(allow_scripts=False))

    # Should pass with allow_scripts
    metadata = validate_skill_directory(skill_dir, policy=ScriptPolicy(allow_scripts=True))
    assert metadata.name == "my-skill"
