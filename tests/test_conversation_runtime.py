from __future__ import annotations

from types import SimpleNamespace

from r9s.conversation.models import ConversationRequest
from r9s.conversation.runtime import content_to_text, run_conversation, stream_conversation


def test_content_to_text_from_mixed_text_blocks() -> None:
    content = [
        {"type": "text", "text": "hello"},
        {"type": "image_url", "image_url": {"url": "x"}},
        SimpleNamespace(type="text", text=" world"),
    ]

    assert content_to_text(content) == "hello world"


def test_run_conversation_normalizes_chat_response(monkeypatch) -> None:
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

    monkeypatch.setattr("r9s.conversation.runtime.R9S", lambda **_: FakeClient())

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


def test_stream_conversation_normalizes_sdk_stream_without_raw_response(monkeypatch) -> None:
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

    monkeypatch.setattr("r9s.conversation.runtime.R9S", lambda **_: FakeClient())

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
