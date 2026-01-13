from __future__ import annotations

from r9s.agents.local_store import LocalAgentStore, load_agent, load_version


def test_agent_store_create_update(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("R9S_AGENTS_DIR", str(tmp_path))
    store = LocalAgentStore()
    store.create(
        "support",
        instructions="Hello {{company}}",
        model="gpt-test",
        change_reason="init",
    )
    loaded = load_agent("support")
    assert loaded.current_version == "1.0.0"
    version = load_version("support", "1.0.0")
    assert version.model == "gpt-test"

    updated = store.update(
        "support",
        instructions="Updated",
        bump="minor",
        change_reason="edit",
    )
    assert updated.version == "1.1.0"
    assert load_agent("support").current_version == "1.1.0"
