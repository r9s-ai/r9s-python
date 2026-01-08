"""Tests for agent-skills integration."""
from __future__ import annotations

from pathlib import Path

import pytest

from r9s.agents.local_store import LocalAgentStore
from r9s.agents.models import AgentVersion


def test_agent_create_with_skills(tmp_path: Path, monkeypatch) -> None:
    """Create agent with skills list."""
    monkeypatch.setenv("R9S_AGENTS_DIR", str(tmp_path))

    store = LocalAgentStore()
    agent = store.create(
        "test-agent",
        instructions="You are helpful.",
        model="gpt-4",
        skills=["code-review", "git-helper"],
    )

    assert agent.name == "test-agent"

    version = store.get_version("test-agent", "1.0.0")
    assert version.skills == ["code-review", "git-helper"]


def test_agent_create_without_skills(tmp_path: Path, monkeypatch) -> None:
    """Create agent without skills defaults to empty list."""
    monkeypatch.setenv("R9S_AGENTS_DIR", str(tmp_path))

    store = LocalAgentStore()
    agent = store.create(
        "no-skills-agent",
        instructions="You are helpful.",
        model="gpt-4",
    )

    version = store.get_version("no-skills-agent", "1.0.0")
    assert version.skills == []


def test_agent_update_with_skills(tmp_path: Path, monkeypatch) -> None:
    """Update agent to add skills."""
    monkeypatch.setenv("R9S_AGENTS_DIR", str(tmp_path))

    store = LocalAgentStore()
    store.create(
        "update-test",
        instructions="You are helpful.",
        model="gpt-4",
        skills=["old-skill"],
    )

    version = store.update(
        "update-test",
        instructions="You are still helpful.",
        skills=["new-skill-a", "new-skill-b"],
    )

    assert version.skills == ["new-skill-a", "new-skill-b"]


def test_agent_update_preserves_skills_if_not_specified(
    tmp_path: Path, monkeypatch
) -> None:
    """Update without skills kwarg preserves existing skills."""
    monkeypatch.setenv("R9S_AGENTS_DIR", str(tmp_path))

    store = LocalAgentStore()
    store.create(
        "preserve-test",
        instructions="You are helpful.",
        model="gpt-4",
        skills=["keep-this-skill"],
    )

    # Update without specifying skills
    version = store.update(
        "preserve-test",
        instructions="Updated instructions.",
    )

    assert version.skills == ["keep-this-skill"]


def test_agent_version_skills_in_hash(tmp_path: Path, monkeypatch) -> None:
    """Skills are included in content hash."""
    monkeypatch.setenv("R9S_AGENTS_DIR", str(tmp_path))

    store = LocalAgentStore()

    # Create two agents with same instructions but different skills
    store.create(
        "agent-a",
        instructions="Same instructions",
        model="gpt-4",
        skills=["skill-a"],
    )
    store.create(
        "agent-b",
        instructions="Same instructions",
        model="gpt-4",
        skills=["skill-b"],
    )

    version_a = store.get_version("agent-a", "1.0.0")
    version_b = store.get_version("agent-b", "1.0.0")

    # Content hashes should differ due to different skills
    assert version_a.content_hash != version_b.content_hash


def test_agent_version_toml_roundtrip(tmp_path: Path, monkeypatch) -> None:
    """Skills survive TOML save/load roundtrip."""
    monkeypatch.setenv("R9S_AGENTS_DIR", str(tmp_path))

    store = LocalAgentStore()
    store.create(
        "roundtrip-test",
        instructions="Test instructions",
        model="gpt-4",
        skills=["skill-one", "skill-two", "skill-three"],
    )

    # Load fresh from disk
    store2 = LocalAgentStore()
    version = store2.get_version("roundtrip-test", "1.0.0")

    assert version.skills == ["skill-one", "skill-two", "skill-three"]
