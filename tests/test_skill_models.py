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
    assert policy.allow_network is False
    assert policy.allow_filesystem is False
    assert policy.allow_env_vars is False
    assert policy.timeout_seconds == 30
    assert policy.allowed_commands == []
