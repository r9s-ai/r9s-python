from __future__ import annotations

import json
from typing import Any

import httpx

from r9s.client import R9S


def _json_response(status_code: int, payload: dict[str, Any]) -> httpx.Response:
    return httpx.Response(
        status_code,
        headers={"content-type": "application/json"},
        content=json.dumps(payload).encode(),
    )


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

    def build_request(self, method: str, url: Any, **kwargs: Any) -> httpx.Request:
        kwargs.pop("timeout", None)
        return httpx.Request(method, url, **kwargs)

    async def send(
        self, request: httpx.Request, *, stream: bool = False, **_: Any
    ) -> httpx.Response:
        return httpx.Response(
            self.response.status_code,
            headers=self.response.headers,
            content=self.response.content,
            request=request,
        )

    async def aclose(self) -> None:
        return None


def _sdk(response: httpx.Response) -> tuple[R9S, _HttpClientStub]:
    client = _HttpClientStub(response)
    async_client = _AsyncHttpClientStub(response)
    r9s = R9S(
        api_key="secret-key",
        server_url="https://api.r9s.ai/v1",
        client=client,
        async_client=async_client,
    )
    return r9s, client


def test_models_list_serializes_expand_and_repeated_filter_query_params() -> None:
    r9s, client = _sdk(_json_response(200, {"object": "list", "data": []}))

    r9s.models.list(
        expand="all",
        filter=["channel=*open*", "endpoint=/v1/messages"],
    )

    assert client.last_request is not None
    assert str(client.last_request.url) == (
        "https://api.r9s.ai/v1/models"
        "?expand=all&filter=channel%3D%2Aopen%2A&filter=endpoint%3D%2Fv1%2Fmessages"
    )


def test_models_list_parses_expanded_fields_into_model() -> None:
    payload = {
        "object": "list",
        "data": [
            {
                "id": "m1",
                "object": "model",
                "created": 1700000000,
                "owned_by": "custom",
                "modality": "text+image->text",
                "context_length": 200000,
                "channels": ["OpenAI", "Relay"],
                "endpoints": ["/v1/messages", "/v1/responses"],
            }
        ],
    }
    r9s, _ = _sdk(_json_response(200, payload))

    response = r9s.models.list(expand="all")

    assert response.data[0].modality == "text+image->text"
    assert response.data[0].context_length == 200000
    assert response.data[0].channels == ["OpenAI", "Relay"]
    assert response.data[0].endpoints == ["/v1/messages", "/v1/responses"]
