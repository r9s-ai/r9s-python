from __future__ import annotations

import pytest

from r9s import R9S


def test_anthropic_messages_supports_system_blocks_and_mcp_servers(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured: dict[str, object] = {}

    def fake_serialize_request_body(request_body, *_args, **_kwargs):
        captured["request_body"] = request_body

        class _Body:
            media_type = "application/json"
            content = b"{}"
            data = {}
            files = []

        return _Body()

    def fake_do_request(self, **_kwargs):
        raise RuntimeError("stop after capturing request")

    monkeypatch.setattr("r9s.messages.utils.serialize_request_body", fake_serialize_request_body)
    monkeypatch.setattr("r9s.messages.Messages.do_request", fake_do_request)

    client = R9S(api_key="test")

    with pytest.raises(RuntimeError, match="stop after capturing request"):
        client.messages.create(
            model="claude-sonnet-4.5",
            max_tokens=256,
            system=[{"type": "text", "text": "Be concise."}],
            messages=[{"role": "user", "content": [{"type": "text", "text": "hi"}]}],
            mcp_servers=[
                {
                    "type": "url",
                    "url": "https://mcp.example.com",
                    "name": "example-mcp",
                }
            ],
        )

    request_body = captured["request_body"]
    assert request_body.system == [{"type": "text", "text": "Be concise."}]
    assert request_body.mcp_servers == [
        {
            "type": "url",
            "url": "https://mcp.example.com",
            "name": "example-mcp",
        }
    ]


def test_anthropic_messages_supports_builtin_tools_container_and_context_management(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured: dict[str, object] = {}

    def fake_serialize_request_body(request_body, *_args, **_kwargs):
        captured["request_body"] = request_body

        class _Body:
            media_type = "application/json"
            content = b"{}"
            data = {}
            files = []

        return _Body()

    def fake_do_request(self, **_kwargs):
        raise RuntimeError("stop after capturing request")

    monkeypatch.setattr("r9s.messages.utils.serialize_request_body", fake_serialize_request_body)
    monkeypatch.setattr("r9s.messages.Messages.do_request", fake_do_request)

    client = R9S(api_key="test")

    with pytest.raises(RuntimeError, match="stop after capturing request"):
        client.messages.create(
            model="claude-sonnet-4.5",
            max_tokens=256,
            messages=[{"role": "user", "content": [{"type": "text", "text": "run code"}]}],
            tools=[{"type": "code_execution_20250825", "name": "code_execution"}],
            container={"type": "auto"},
            context_management={"edits": [{"operation": "keep"}]},
        )

    request_body = captured["request_body"]
    dumped = request_body.model_dump(by_alias=True, exclude_none=True)
    assert dumped["tools"] == [{"type": "code_execution_20250825", "name": "code_execution"}]
    assert dumped["container"] == {"type": "auto"}
    assert dumped["context_management"] == {"edits": [{"operation": "keep"}]}
