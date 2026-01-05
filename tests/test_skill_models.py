from __future__ import annotations

from r9s.skills.models import ScriptPolicy, Skill, SkillMetadata


def test_skill_models_defaults() -> None:
    metadata = SkillMetadata(name="code-review", description="Review code")
    assert metadata.allowed_tools == []
    assert metadata.metadata == {}

    skill = Skill(
        name="code-review",
        description="Review code",
        instructions="Do the thing",
        source="local",
    )
    assert skill.allowed_tools == []
    assert skill.scripts == []

    policy = ScriptPolicy()
    assert policy.allow_scripts is False
