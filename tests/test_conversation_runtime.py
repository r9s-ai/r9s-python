from __future__ import annotations

from types import SimpleNamespace

import pytest

from r9s.conversation.models import ConversationRequest
from r9s.conversation.adapter import (
    _adapt_request_to_anthropic_messages_kwargs,
    _adapt_request_to_gemini_generate_content_kwargs,
    content_to_text,
    resolve_conversation_protocol,
    run_conversation,
    stream_conversation,
    will_apply_default_anthropic_max_tokens,
)

PNG_DATA_URL = "data:image/png;base64,ZmFrZQ=="


def test_content_to_text_from_mixed_text_blocks() -> None:
    content = [
        {"type": "text", "text": "hello"},
        {"type": "image_url", "image_url": {"url": "x"}},
        SimpleNamespace(type="text", text=" world"),
    ]

    assert content_to_text(content) == "hello world"


def test_resolve_conversation_protocol_from_explicit_endpoints() -> None:
    anthropic_request = ConversationRequest(
        api_key="k",
        base_url="https://example.com",
        model="demo",
        model_endpoints=["/v1/messages"],
        messages=[{"role": "user", "content": "hi"}],
    )
    gemini_request = ConversationRequest(
        api_key="k",
        base_url="https://example.com",
        model="demo",
        model_endpoints=["/v1beta/models/gemini-2.5-flash:streamGenerateContent?alt=sse"],
        messages=[{"role": "user", "content": "hi"}],
    )

    assert resolve_conversation_protocol(anthropic_request) == "anthropic_messages"
    assert resolve_conversation_protocol(gemini_request) == "gemini_generate_content"


def test_resolve_conversation_protocol_prefers_chat_completions_when_multiple_routes_exist() -> None:
    request = ConversationRequest(
        api_key="k",
        base_url="https://example.com",
        model="demo",
        model_endpoints=[
            "/v1/messages",
            "/v1/chat/completions",
            "/v1beta/models/gemini-2.5-flash:generateContent",
        ],
        messages=[{"role": "user", "content": "hi"}],
    )

    assert resolve_conversation_protocol(request) == "chat_completions"


def test_adapt_request_to_anthropic_messages_kwargs_converts_system_text_and_image() -> None:
    request = ConversationRequest(
        api_key="k",
        base_url="https://example.com",
        model="claude-3-7-sonnet",
        messages=[
            {"role": "system", "content": "be helpful"},
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": "look"},
                    {"type": "image_url", "image_url": {"url": PNG_DATA_URL}},
                ],
            },
        ],
        max_tokens=256,
        temperature=0.2,
    )

    kwargs = _adapt_request_to_anthropic_messages_kwargs(request, stream=False)

    assert kwargs["system"] == "be helpful"
    assert kwargs["max_tokens"] == 256
    assert kwargs["temperature"] == 0.2
    assert kwargs["messages"][0]["role"] == "user"
    assert kwargs["messages"][0]["content"][0] == {"type": "text", "text": "look"}
    assert kwargs["messages"][0]["content"][1]["source"]["media_type"] == "image/png"
    assert kwargs["messages"][0]["content"][1]["source"]["data"] == "ZmFrZQ=="


def test_adapt_request_to_anthropic_messages_kwargs_uses_default_max_tokens() -> None:
    request = ConversationRequest(
        api_key="k",
        base_url="https://example.com",
        model="claude-3-7-sonnet",
        messages=[{"role": "user", "content": "hi"}],
    )

    kwargs = _adapt_request_to_anthropic_messages_kwargs(request, stream=False)

    assert kwargs["max_tokens"] == 4096
    assert will_apply_default_anthropic_max_tokens(request) is True


def test_adapt_request_to_gemini_generate_content_kwargs_converts_system_text_and_image() -> None:
    request = ConversationRequest(
        api_key="k",
        base_url="https://example.com",
        model="gemini-2.5-flash",
        messages=[
            {"role": "system", "content": "be helpful"},
            {"role": "assistant", "content": "previous reply"},
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": "look"},
                    {"type": "image_url", "image_url": {"url": PNG_DATA_URL}},
                ],
            },
        ],
        max_tokens=512,
        temperature=0.1,
        top_p=0.9,
        presence_penalty=0.3,
        frequency_penalty=0.4,
    )

    kwargs = _adapt_request_to_gemini_generate_content_kwargs(request)

    assert kwargs["system_instruction"] == {"parts": [{"text": "be helpful"}]}
    assert kwargs["contents"][0] == {"role": "model", "parts": [{"text": "previous reply"}]}
    assert kwargs["contents"][1]["role"] == "user"
    assert kwargs["contents"][1]["parts"][0] == {"text": "look"}
    assert kwargs["contents"][1]["parts"][1]["inline_data"]["mime_type"] == "image/png"
    assert kwargs["generation_config"] == {
        "temperature": 0.1,
        "topP": 0.9,
        "maxOutputTokens": 512,
        "presencePenalty": 0.3,
        "frequencyPenalty": 0.4,
    }


def test_run_conversation_normalizes_chat_response(monkeypatch: pytest.MonkeyPatch) -> None:
    response = SimpleNamespace(
        id="resp_123",
        choices=[SimpleNamespace(message=SimpleNamespace(content=[{"type": "text", "text": "ok"}]))],
        usage=SimpleNamespace(prompt_tokens=11, completion_tokens=7),
    )

    class FakeClient:
        def __enter__(self) -> "FakeClient":
            self.chat = SimpleNamespace(create=lambda **_: response)
            return self

        def __exit__(self, exc_type, exc, tb) -> None:
            return None

    monkeypatch.setattr("r9s.conversation.adapter.R9S", lambda **_: FakeClient())

    result = run_conversation(
        ConversationRequest(
            api_key="k",
            base_url="https://example.com",
            model="demo",
            messages=[{"role": "user", "content": "hi"}],
        )
    )

    assert result.text == "ok"
    assert result.request_id == "resp_123"
    assert result.input_tokens == 11
    assert result.output_tokens == 7


def test_run_conversation_normalizes_anthropic_response(monkeypatch: pytest.MonkeyPatch) -> None:
    response = SimpleNamespace(
        id="msg_123",
        content=[SimpleNamespace(type="text", text="hello anth")],
        usage=SimpleNamespace(input_tokens=13, output_tokens=5),
    )

    class FakeClient:
        def __enter__(self) -> "FakeClient":
            self.messages = SimpleNamespace(create=lambda **_: response)
            return self

        def __exit__(self, exc_type, exc, tb) -> None:
            return None

    monkeypatch.setattr("r9s.conversation.adapter.R9S", lambda **_: FakeClient())

    result = run_conversation(
        ConversationRequest(
            api_key="k",
            base_url="https://example.com",
            model="claude-3-7-sonnet",
            model_endpoints=["/v1/messages"],
            messages=[{"role": "user", "content": "hi"}],
        )
    )

    assert result.text == "hello anth"
    assert result.request_id == "msg_123"
    assert result.input_tokens == 13
    assert result.output_tokens == 5
    assert result.protocol == "anthropic_messages"


def test_run_conversation_normalizes_gemini_response(monkeypatch: pytest.MonkeyPatch) -> None:
    response = SimpleNamespace(
        response_id="gem_123",
        candidates=[SimpleNamespace(content=SimpleNamespace(parts=[{"text": "hello gemini"}]))],
        usage_metadata=SimpleNamespace(prompt_token_count=9, candidates_token_count=4),
    )

    class FakeClient:
        def __enter__(self) -> "FakeClient":
            self.gemini = SimpleNamespace(generate_content=lambda **_: response)
            return self

        def __exit__(self, exc_type, exc, tb) -> None:
            return None

    monkeypatch.setattr("r9s.conversation.adapter.R9S", lambda **_: FakeClient())

    result = run_conversation(
        ConversationRequest(
            api_key="k",
            base_url="https://example.com",
            model="gemini-2.5-flash",
            model_endpoints=["/v1beta/models/gemini-2.5-flash:generateContent"],
            messages=[{"role": "user", "content": "hi"}],
        )
    )

    assert result.text == "hello gemini"
    assert result.request_id == "gem_123"
    assert result.input_tokens == 9
    assert result.output_tokens == 4
    assert result.protocol == "gemini_generate_content"


def test_stream_conversation_normalizes_sdk_stream_without_raw_response(monkeypatch: pytest.MonkeyPatch) -> None:
    stream = SimpleNamespace(
        response=None,
        __iter__=lambda self: iter(
            [
                SimpleNamespace(
                    id="evt_1",
                    usage=SimpleNamespace(prompt_tokens=3, completion_tokens=0),
                    choices=[SimpleNamespace(delta=SimpleNamespace(content="hel"))],
                ),
                SimpleNamespace(
                    id="evt_1",
                    usage=SimpleNamespace(prompt_tokens=3, completion_tokens=2),
                    choices=[SimpleNamespace(delta=SimpleNamespace(content="lo"))],
                ),
            ]
        ),
    )

    class FakeStream:
        response = None

        def __iter__(self):
            return iter(stream.__iter__(stream))

    class FakeClient:
        def __enter__(self) -> "FakeClient":
            self.chat = SimpleNamespace(create=lambda **_: FakeStream())
            return self

        def __exit__(self, exc_type, exc, tb) -> None:
            return None

    monkeypatch.setattr("r9s.conversation.adapter.R9S", lambda **_: FakeClient())

    events = list(
        stream_conversation(
            ConversationRequest(
                api_key="k",
                base_url="https://example.com",
                model="demo",
                messages=[{"role": "user", "content": "hi"}],
            )
        )
    )

    assert [event.type for event in events] == ["text_delta", "text_delta", "done"]
    assert [event.text for event in events[:2]] == ["hel", "lo"]
    assert events[-1].request_id == "evt_1"
    assert events[-1].input_tokens == 3
    assert events[-1].output_tokens == 2


def test_stream_conversation_normalizes_anthropic_stream(monkeypatch: pytest.MonkeyPatch) -> None:
    stream_events = [
        SimpleNamespace(
            TYPE="message_start",
            message=SimpleNamespace(
                id="msg_stream_1",
                usage=SimpleNamespace(input_tokens=6, output_tokens=0),
            ),
        ),
        SimpleNamespace(
            TYPE="content_block_delta",
            delta=SimpleNamespace(type="text_delta", text="hello "),
        ),
        SimpleNamespace(
            TYPE="message_delta",
            usage=SimpleNamespace(output_tokens=2),
        ),
        SimpleNamespace(
            TYPE="content_block_delta",
            delta=SimpleNamespace(type="text_delta", text="anthropic"),
        ),
        SimpleNamespace(TYPE="message_stop"),
    ]

    class FakeClient:
        def __enter__(self) -> "FakeClient":
            self.messages = SimpleNamespace(create=lambda **_: iter(stream_events))
            return self

        def __exit__(self, exc_type, exc, tb) -> None:
            return None

    monkeypatch.setattr("r9s.conversation.adapter.R9S", lambda **_: FakeClient())

    events = list(
        stream_conversation(
            ConversationRequest(
                api_key="k",
                base_url="https://example.com",
                model="claude-3-7-sonnet",
                model_endpoints=["/v1/messages"],
                messages=[{"role": "user", "content": "hi"}],
            )
        )
    )

    assert [event.type for event in events] == ["text_delta", "text_delta", "done"]
    assert [event.text for event in events[:2]] == ["hello ", "anthropic"]
    assert events[-1].request_id == "msg_stream_1"
    assert events[-1].input_tokens == 6
    assert events[-1].output_tokens == 2


def test_stream_conversation_normalizes_gemini_stream(monkeypatch: pytest.MonkeyPatch) -> None:
    stream_events = [
        SimpleNamespace(
            response_id="gem_stream_1",
            candidates=[SimpleNamespace(content=SimpleNamespace(parts=[{"text": "hello "}]))],
            usage_metadata=SimpleNamespace(prompt_token_count=8, candidates_token_count=1),
        ),
        SimpleNamespace(
            response_id="gem_stream_1",
            candidates=[SimpleNamespace(content=SimpleNamespace(parts=[{"text": "gemini"}]))],
            usage_metadata=SimpleNamespace(prompt_token_count=8, candidates_token_count=2),
        ),
    ]

    class FakeClient:
        def __enter__(self) -> "FakeClient":
            self.gemini = SimpleNamespace(stream_generate_content=lambda **_: iter(stream_events))
            return self

        def __exit__(self, exc_type, exc, tb) -> None:
            return None

    monkeypatch.setattr("r9s.conversation.adapter.R9S", lambda **_: FakeClient())

    events = list(
        stream_conversation(
            ConversationRequest(
                api_key="k",
                base_url="https://example.com",
                model="gemini-2.5-flash",
                model_endpoints=["/v1beta/models/gemini-2.5-flash:generateContent"],
                messages=[{"role": "user", "content": "hi"}],
            )
        )
    )

    assert [event.type for event in events] == ["text_delta", "text_delta", "done"]
    assert [event.text for event in events[:2]] == ["hello ", "gemini"]
    assert events[-1].request_id == "gem_stream_1"
    assert events[-1].input_tokens == 8
    assert events[-1].output_tokens == 2


def test_anthropic_adapter_rejects_tool_messages() -> None:
    request = ConversationRequest(
        api_key="k",
        base_url="https://example.com",
        model="claude-3-7-sonnet",
        messages=[{"role": "tool", "content": "{}"}],
    )

    with pytest.raises(ValueError, match="tool messages"):
        _adapt_request_to_anthropic_messages_kwargs(request, stream=False)
