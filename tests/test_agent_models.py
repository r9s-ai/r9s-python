from __future__ import annotations

from r9s.agents.models import AgentVersion


def test_agent_version_hash_and_vars() -> None:
    version = AgentVersion(
        version="1.0.0",
        instructions="Hello {{company}}",
        model="gpt-test",
    )
    assert version.variables == ["company"]
    assert version.content_hash.startswith("sha256:")
