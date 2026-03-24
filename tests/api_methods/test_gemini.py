from __future__ import annotations

import json
from typing import Any, Type

import httpx
import pytest

from r9s import errors
from r9s.client import R9S
from r9s.models.gemini_models import GeminiGenerateContentResponse


def _json_response(status_code: int, payload: dict[str, Any]) -> httpx.Response:
    return httpx.Response(
        status_code,
        headers={"content-type": "application/json"},
        content=json.dumps(payload).encode(),
    )


def _sse_response(*events: dict[str, Any]) -> httpx.Response:
    chunks = [f"data: {json.dumps(event)}\n\n" for event in events]
    return httpx.Response(
        200,
        headers={"content-type": "text/event-stream"},
        content="".join(chunks).encode(),
    )


def _error_payload(message: str, status: int) -> dict[str, Any]:
    return {
        "error": {"message": message, "type": "api_error", "code": None},
        "status": str(status),
    }


def _request_json(request: httpx.Request) -> dict[str, Any]:
    return json.loads(request.content.decode())


class _HttpClientStub:
    def __init__(self, response: httpx.Response) -> None:
        self.response = response
        self.last_request: httpx.Request | None = None

    def build_request(self, method: str, url: Any, **kwargs: Any) -> httpx.Request:
        kwargs.pop("timeout", None)
        return httpx.Request(method, url, **kwargs)

    def send(
        self, request: httpx.Request, *, stream: bool = False, **_: Any
    ) -> httpx.Response:
        self.last_request = request
        return httpx.Response(
            self.response.status_code,
            headers=self.response.headers,
            content=self.response.content,
            request=request,
        )

    def close(self) -> None:
        return None


class _AsyncHttpClientStub:
    def __init__(self, response: httpx.Response) -> None:
        self.response = response
        self.last_request: httpx.Request | None = None

    def build_request(self, method: str, url: Any, **kwargs: Any) -> httpx.Request:
        kwargs.pop("timeout", None)
        return httpx.Request(method, url, **kwargs)

    async def send(
        self, request: httpx.Request, *, stream: bool = False, **_: Any
    ) -> httpx.Response:
        self.last_request = request
        return httpx.Response(
            self.response.status_code,
            headers=self.response.headers,
            content=self.response.content,
            request=request,
        )

    async def aclose(self) -> None:
        return None


def _sdk(
    response: httpx.Response,
    *,
    api_key: Any = "secret-key",
    server_url: str = "https://api.r9s.ai/v1",
) -> tuple[R9S, _HttpClientStub, _AsyncHttpClientStub]:
    client = _HttpClientStub(response)
    async_client = _AsyncHttpClientStub(response)
    r9s = R9S(
        api_key=api_key,
        server_url=server_url,
        client=client,
        async_client=async_client,
    )
    return r9s, client, async_client


def test_gemini_generate_content_uses_x_goog_api_key_and_preserves_model_name() -> None:
    r9s, client, _ = _sdk(_json_response(200, {"responseId": "resp-1", "candidates": []}))

    res = r9s.gemini.generate_content(
        model="models/gemini-3-flash",
        contents=[{"parts": [{"text": "hello"}]}],
    )

    assert isinstance(res, GeminiGenerateContentResponse)
    assert client.last_request is not None
    assert (
        str(client.last_request.url)
        == "https://api.r9s.ai/v1beta/models/models%2Fgemini-3-flash:generateContent"
    )
    assert client.last_request.headers["x-goog-api-key"] == "secret-key"
    assert "authorization" not in client.last_request.headers


def test_gemini_generate_content_serializes_full_request_payload() -> None:
    r9s, client, _ = _sdk(_json_response(200, {"responseId": "resp-1", "candidates": []}))

    r9s.gemini.generate_content(
        model="gemini-3-flash",
        contents=[{"role": "user", "parts": [{"text": "hello"}]}],
        generation_config={
            "temperature": 0.7,
            "topP": 0.9,
            "maxOutputTokens": 256,
            "responseMimeType": "application/json",
        },
        safety_settings=[
            {
                "category": "HARM_CATEGORY_HATE_SPEECH",
                "threshold": "BLOCK_MEDIUM_AND_ABOVE",
            }
        ],
        system_instruction={"parts": [{"text": "Be concise"}]},
        tools=[
            {
                "functionDeclarations": [
                    {
                        "name": "lookup_weather",
                        "description": "Get the weather",
                        "parameters": {"type": "object"},
                    }
                ]
            }
        ],
        tool_config={"functionCallingConfig": {"mode": "AUTO"}},
        cached_content="cachedContents/abc123",
        store=True,
        http_headers={"x-test-header": "test-value"},
    )

    assert client.last_request is not None
    body = _request_json(client.last_request)
    assert body["contents"][0]["role"] == "user"
    assert body["generationConfig"]["temperature"] == 0.7
    assert body["generationConfig"]["topP"] == 0.9
    assert body["generationConfig"]["maxOutputTokens"] == 256
    assert body["generationConfig"]["responseMimeType"] == "application/json"
    assert body["safetySettings"][0]["category"] == "HARM_CATEGORY_HATE_SPEECH"
    assert body["systemInstruction"]["parts"][0]["text"] == "Be concise"
    assert body["tools"][0]["functionDeclarations"][0]["name"] == "lookup_weather"
    assert body["toolConfig"]["functionCallingConfig"]["mode"] == "AUTO"
    assert body["cachedContent"] == "cachedContents/abc123"
    assert body["store"] is True
    assert client.last_request.headers["x-test-header"] == "test-value"


def test_gemini_generate_content_uses_server_url_override() -> None:
    r9s, client, _ = _sdk(
        _json_response(200, {"responseId": "resp-1", "candidates": []}),
        server_url="https://api.r9s.ai/base",
    )

    r9s.gemini.generate_content(
        model="gemini-3-flash",
        contents=[{"parts": [{"text": "hello"}]}],
        server_url="https://generativelanguage.googleapis.com",
    )

    assert client.last_request is not None
    assert (
        str(client.last_request.url)
        == "https://generativelanguage.googleapis.com/v1beta/models/gemini-3-flash:generateContent"
    )


def test_gemini_generate_content_keeps_non_v1_base_url_unchanged() -> None:
    r9s, client, _ = _sdk(
        _json_response(200, {"responseId": "resp-1", "candidates": []}),
        server_url="https://example.com/custom-base",
    )

    r9s.gemini.generate_content(
        model="gemini-3-flash",
        contents=[{"parts": [{"text": "hello"}]}],
    )

    assert client.last_request is not None
    assert (
        str(client.last_request.url)
        == "https://example.com/custom-base/v1beta/models/gemini-3-flash:generateContent"
    )


def test_gemini_generate_content_supports_callable_api_key() -> None:
    r9s, client, _ = _sdk(
        _json_response(200, {"responseId": "resp-1", "candidates": []}),
        api_key=lambda: "callable-key",
    )

    r9s.gemini.generate_content(
        model="gemini-3-flash",
        contents=[{"parts": [{"text": "hello"}]}],
    )

    assert client.last_request is not None
    assert client.last_request.headers["x-goog-api-key"] == "callable-key"


def test_gemini_generate_content_rejects_missing_api_key() -> None:
    r9s, _, _ = _sdk(
        _json_response(200, {"responseId": "resp-1", "candidates": []}),
        api_key="",
    )

    with pytest.raises(ValueError, match="api_key is required"):
        r9s.gemini.generate_content(
            model="gemini-3-flash",
            contents=[{"parts": [{"text": "hello"}]}],
        )


def test_gemini_stream_generate_content_returns_event_stream_for_multiple_events() -> None:
    r9s, client, _ = _sdk(
        _sse_response(
            {"responseId": "resp-1", "candidates": [{"content": {"role": "model", "parts": [{"text": "Hi"}]}}]},
            {"responseId": "resp-2", "candidates": [{"content": {"role": "model", "parts": [{"text": " there"}]}}]},
        ),
        api_key="Bearer secret-key",
    )

    stream = r9s.gemini.stream_generate_content(
        model="gemini-3-flash",
        contents=[{"parts": [{"text": "hello"}]}],
    )
    events = list(stream)

    assert [event.response_id for event in events] == ["resp-1", "resp-2"]
    assert client.last_request is not None
    assert client.last_request.headers["x-goog-api-key"] == "secret-key"
    assert (
        str(client.last_request.url)
        == "https://api.r9s.ai/v1beta/models/gemini-3-flash:streamGenerateContent?alt=sse"
    )


def test_gemini_generate_content_parses_response_fields() -> None:
    payload = {
        "responseId": "resp-1",
        "modelVersion": "gemini-3-flash-001",
        "usageMetadata": {"promptTokenCount": 12, "candidatesTokenCount": 5, "totalTokenCount": 17},
        "candidates": [
            {
                "finishReason": "STOP",
                "content": {"role": "model", "parts": [{"text": "done"}]},
            }
        ],
    }
    r9s, _, _ = _sdk(_json_response(200, payload))

    res = r9s.gemini.generate_content(
        model="gemini-3-flash",
        contents=[{"parts": [{"text": "hello"}]}],
    )

    assert res.response_id == "resp-1"
    assert res.model_version == "gemini-3-flash-001"
    assert res.usage_metadata is not None
    assert res.usage_metadata.total_token_count == 17
    assert res.candidates is not None
    assert res.candidates[0].finish_reason == "STOP"
    assert res.candidates[0].content is not None
    assert res.candidates[0].content.parts[0]["text"] == "done"


@pytest.mark.parametrize(
    ("status_code", "exc_type"),
    [
        (400, errors.BadRequestError),
        (401, errors.AuthenticationError),
        (403, errors.PermissionDeniedError),
        (422, errors.UnprocessableEntityError),
        (429, errors.RateLimitError),
        (500, errors.InternalServerError),
        (503, errors.ServiceUnavailableError),
    ],
)
def test_gemini_generate_content_maps_json_errors(
    status_code: int, exc_type: Type[Exception]
) -> None:
    r9s, _, _ = _sdk(_json_response(status_code, _error_payload("boom", status_code)))

    with pytest.raises(exc_type) as exc_info:
        r9s.gemini.generate_content(
            model="gemini-3-flash",
            contents=[{"parts": [{"text": "hello"}]}],
        )

    assert getattr(exc_info.value, "status_code", None) == status_code
    assert "boom" in getattr(exc_info.value, "body", "")


def test_gemini_generate_content_maps_generic_4xx_to_default_error() -> None:
    r9s, _, _ = _sdk(
        httpx.Response(
            418,
            headers={"content-type": "text/plain"},
            content=b"teapot",
        )
    )

    with pytest.raises(errors.R9SDefaultError) as exc_info:
        r9s.gemini.generate_content(
            model="gemini-3-flash",
            contents=[{"parts": [{"text": "hello"}]}],
        )

    assert exc_info.value.status_code == 418
    assert "teapot" in exc_info.value.body


def test_gemini_stream_generate_content_rejects_json_response() -> None:
    r9s, _, _ = _sdk(_json_response(200, {"responseId": "resp-1", "candidates": []}))

    with pytest.raises(errors.R9SDefaultError, match="Expected Gemini SSE response"):
        r9s.gemini.stream_generate_content(
            model="gemini-3-flash",
            contents=[{"parts": [{"text": "hello"}]}],
        )


@pytest.mark.asyncio
async def test_gemini_generate_content_async_uses_x_goog_api_key_and_parses_response() -> None:
    payload = {
        "responseId": "resp-async",
        "usageMetadata": {"totalTokenCount": 9},
        "candidates": [],
    }
    r9s, _, async_client = _sdk(_json_response(200, payload))

    res = await r9s.gemini.generate_content_async(
        model="gemini-3-flash",
        contents=[{"parts": [{"text": "hello"}]}],
    )

    assert isinstance(res, GeminiGenerateContentResponse)
    assert res.response_id == "resp-async"
    assert res.usage_metadata is not None
    assert res.usage_metadata.total_token_count == 9
    assert async_client.last_request is not None
    assert async_client.last_request.headers["x-goog-api-key"] == "secret-key"


@pytest.mark.asyncio
async def test_gemini_stream_generate_content_async_returns_multiple_events() -> None:
    r9s, _, async_client = _sdk(
        _sse_response(
            {"responseId": "resp-async-1", "candidates": [{"content": {"role": "model", "parts": [{"text": "Hi"}]}}]},
            {"responseId": "resp-async-2", "candidates": [{"content": {"role": "model", "parts": [{"text": " again"}]}}]},
        )
    )

    stream = await r9s.gemini.stream_generate_content_async(
        model="gemini-3-flash",
        contents=[{"parts": [{"text": "hello"}]}],
    )
    events = [event async for event in stream]

    assert [event.response_id for event in events] == ["resp-async-1", "resp-async-2"]
    assert async_client.last_request is not None
    assert async_client.last_request.headers["x-goog-api-key"] == "secret-key"


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("status_code", "exc_type"),
    [
        (400, errors.BadRequestError),
        (401, errors.AuthenticationError),
        (403, errors.PermissionDeniedError),
        (422, errors.UnprocessableEntityError),
        (429, errors.RateLimitError),
        (500, errors.InternalServerError),
        (503, errors.ServiceUnavailableError),
    ],
)
async def test_gemini_generate_content_async_maps_json_errors(
    status_code: int, exc_type: Type[Exception]
) -> None:
    r9s, _, _ = _sdk(_json_response(status_code, _error_payload("boom-async", status_code)))

    with pytest.raises(exc_type) as exc_info:
        await r9s.gemini.generate_content_async(
            model="gemini-3-flash",
            contents=[{"parts": [{"text": "hello"}]}],
        )

    assert getattr(exc_info.value, "status_code", None) == status_code
    assert "boom-async" in getattr(exc_info.value, "body", "")


@pytest.mark.asyncio
async def test_gemini_stream_generate_content_async_rejects_json_response() -> None:
    r9s, _, _ = _sdk(_json_response(200, {"responseId": "resp-1", "candidates": []}))

    with pytest.raises(errors.R9SDefaultError, match="Expected Gemini SSE response"):
        await r9s.gemini.stream_generate_content_async(
            model="gemini-3-flash",
            contents=[{"parts": [{"text": "hello"}]}],
        )
