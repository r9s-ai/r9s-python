"""Tests for skills loader module (agent integration)."""
from __future__ import annotations

from pathlib import Path

import pytest

from r9s.skills.loader import (
    build_system_prompt_with_skills,
    format_skills_context,
    load_skills,
    resolve_skill_script,
)
from r9s.skills.models import Skill


def test_format_skills_context_empty() -> None:
    """Empty skills list returns empty string."""
    result = format_skills_context([])
    assert result == ""


def test_format_skills_context_single() -> None:
    """Single skill is formatted correctly."""
    skill = Skill(
        name="test-skill",
        description="A test skill",
        instructions="Do the test thing.",
        source="local",
    )
    result = format_skills_context([skill])
    assert "## Skills" in result
    assert "### test-skill" in result
    assert "*A test skill*" in result
    assert "Do the test thing." in result


def test_format_skills_context_multiple() -> None:
    """Multiple skills are formatted correctly."""
    skills = [
        Skill(
            name="skill-a",
            description="First skill",
            instructions="Instructions A",
            source="local",
        ),
        Skill(
            name="skill-b",
            description="Second skill",
            instructions="Instructions B",
            source="local",
        ),
    ]
    result = format_skills_context(skills)
    assert "### skill-a" in result
    assert "### skill-b" in result
    assert "Instructions A" in result
    assert "Instructions B" in result


def test_load_skills_local(tmp_path: Path, monkeypatch) -> None:
    """Load local skills by name."""
    monkeypatch.setenv("R9S_SKILLS_DIR", str(tmp_path))

    # Create a test skill
    skill_dir = tmp_path / "my-skill"
    skill_dir.mkdir()
    (skill_dir / "SKILL.md").write_text(
        """---
name: my-skill
description: My test skill
---

# Instructions

Do something useful.
""",
        encoding="utf-8",
    )

    skills = load_skills(["my-skill"])
    assert len(skills) == 1
    assert skills[0].name == "my-skill"
    assert skills[0].description == "My test skill"
    assert "Do something useful" in skills[0].instructions


def test_load_skills_not_found(tmp_path: Path, monkeypatch) -> None:
    """Missing skills are skipped with warning."""
    monkeypatch.setenv("R9S_SKILLS_DIR", str(tmp_path))

    warnings = []
    skills = load_skills(["nonexistent"], warn_fn=warnings.append)
    assert len(skills) == 0
    assert len(warnings) == 1
    assert "not found" in warnings[0].lower()


def test_load_skills_remote_skipped() -> None:
    """Remote skill refs are skipped with warning."""
    warnings = []
    skills = load_skills(
        ["github:owner/repo", "r9s:some-skill", "https://example.com/skill"],
        warn_fn=warnings.append,
    )
    assert len(skills) == 0
    assert len(warnings) == 3
    for w in warnings:
        assert "not yet supported" in w.lower()


def test_build_system_prompt_with_skills_empty() -> None:
    """No skills returns original prompt."""
    result = build_system_prompt_with_skills("You are helpful.", [])
    assert result == "You are helpful."


def test_build_system_prompt_with_skills(tmp_path: Path, monkeypatch) -> None:
    """Skills are appended to system prompt."""
    monkeypatch.setenv("R9S_SKILLS_DIR", str(tmp_path))

    # Create a test skill
    skill_dir = tmp_path / "code-review"
    skill_dir.mkdir()
    (skill_dir / "SKILL.md").write_text(
        """---
name: code-review
description: Code review expertise
---

Review code for bugs and style.
""",
        encoding="utf-8",
    )

    result = build_system_prompt_with_skills(
        "You are a helpful assistant.",
        ["code-review"],
    )

    assert "You are a helpful assistant." in result
    assert "## Skills" in result
    assert "### code-review" in result
    assert "Review code for bugs and style." in result


def test_build_system_prompt_preserves_base_on_missing_skills(
    tmp_path: Path, monkeypatch
) -> None:
    """If all skills fail to load, return original prompt."""
    monkeypatch.setenv("R9S_SKILLS_DIR", str(tmp_path))

    warnings = []
    result = build_system_prompt_with_skills(
        "You are helpful.",
        ["nonexistent-skill"],
        warn_fn=warnings.append,
    )

    assert result == "You are helpful."
    assert len(warnings) == 1


def test_resolve_skill_script_valid(tmp_path: Path, monkeypatch) -> None:
    """Resolve a valid script path from skill."""
    monkeypatch.setenv("R9S_SKILLS_DIR", str(tmp_path))

    # Create a skill with a script
    skill_dir = tmp_path / "my-skill"
    scripts_dir = skill_dir / "scripts"
    scripts_dir.mkdir(parents=True)
    (skill_dir / "SKILL.md").write_text(
        """---
name: my-skill
description: Test skill
---
Instructions here.
""",
        encoding="utf-8",
    )
    (scripts_dir / "run.sh").write_text("#!/bin/bash\necho hello\n")

    skill = Skill(
        name="my-skill",
        description="Test skill",
        instructions="Instructions here.",
        source="local",
        scripts=["scripts/run.sh"],
    )

    result = resolve_skill_script("scripts/run.sh", [skill])
    assert result is not None
    assert result.exists()
    assert result.name == "run.sh"


def test_resolve_skill_script_not_found() -> None:
    """Returns None for non-existent script."""
    skill = Skill(
        name="my-skill",
        description="Test skill",
        instructions="Instructions here.",
        source="local",
        scripts=["scripts/other.sh"],
    )

    result = resolve_skill_script("scripts/run.sh", [skill])
    assert result is None


def test_resolve_skill_script_path_traversal(tmp_path: Path, monkeypatch) -> None:
    """Returns None for path traversal attempts."""
    monkeypatch.setenv("R9S_SKILLS_DIR", str(tmp_path))

    # Create a skill directory
    skill_dir = tmp_path / "evil-skill"
    scripts_dir = skill_dir / "scripts"
    scripts_dir.mkdir(parents=True)
    (skill_dir / "SKILL.md").write_text(
        """---
name: evil-skill
description: Evil skill
---
Instructions here.
""",
        encoding="utf-8",
    )

    # Create a file outside the skill directory
    (tmp_path / "secret.txt").write_text("secret data")

    # Skill claims to have a script with path traversal
    skill = Skill(
        name="evil-skill",
        description="Evil skill",
        instructions="Instructions here.",
        source="local",
        scripts=["scripts/../../../secret.txt"],
    )

    # Should return None due to path traversal detection
    result = resolve_skill_script("scripts/../../../secret.txt", [skill])
    assert result is None
