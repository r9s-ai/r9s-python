from __future__ import annotations

from r9s.models.responseobject import ResponseObject
from r9s.models.responserequest import ResponseRequest


def test_response_request_accepts_official_stateful_fields() -> None:
    request = ResponseRequest(
        model="gpt-4o-mini",
        input=[
            {
                "role": "user",
                "content": [{"type": "input_text", "text": "hello"}],
            }
        ],
        include=["file_search_call.results"],
        conversation={"id": "conv_123"},
        max_tool_calls=2,
        prompt={"id": "pmpt_123", "variables": {"topic": "weather"}},
        prompt_cache_key="cache-key",
        prompt_cache_retention="24h",
        safety_identifier="user-42",
        service_tier="priority",
        user="legacy-user",
    )

    assert isinstance(request.input, list)
    assert request.include == ["file_search_call.results"]
    assert request.conversation == "conv_123" or getattr(request.conversation, "id", None) == "conv_123"
    assert request.max_tool_calls == 2
    assert request.prompt is not None
    assert request.prompt.id == "pmpt_123"
    assert request.prompt.variables == {"topic": "weather"}
    assert request.prompt_cache_key == "cache-key"
    assert request.prompt_cache_retention == "24h"
    assert request.safety_identifier == "user-42"
    assert request.service_tier == "priority"
    assert request.user == "legacy-user"


def test_response_object_output_text_aggregates_output_items() -> None:
    response = ResponseObject.model_validate(
        {
            "id": "resp_123",
            "object": "response",
            "created_at": 123,
            "status": "completed",
            "model": "gpt-4o-mini",
            "output": [
                {
                    "id": "msg_1",
                    "type": "message",
                    "status": "completed",
                    "role": "assistant",
                    "content": [
                        {"type": "output_text", "text": "Hello"},
                        {"type": "output_text", "text": " world"},
                    ],
                }
            ],
        }
    )

    assert response.output_text == "Hello world"
