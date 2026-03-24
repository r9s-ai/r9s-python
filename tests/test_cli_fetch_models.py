from __future__ import annotations

from types import SimpleNamespace

import r9s.cli_tools.cli as cli


class _FakeResponse:
    def __init__(self, data):
        self.data = data


class _FakeR9S:
    calls: list[dict[str, object]] = []
    response_data = []

    def __init__(self, *, api_key: str, server_url: str, timeout_ms: int | None = None):
        self.api_key = api_key
        self.server_url = server_url
        self.timeout_ms = timeout_ms
        self.models = SimpleNamespace(list=self._list)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return None

    def _list(self, *, expand=None, filter=None):
        type(self).calls.append(
            {
                "api_key": self.api_key,
                "server_url": self.server_url,
                "timeout_ms": self.timeout_ms,
                "expand": expand,
                "filter": filter,
            }
        )
        return _FakeResponse(type(self).response_data)


def test_fetch_models_uses_sdk_with_endpoints_expand(monkeypatch) -> None:
    _FakeR9S.calls = []
    _FakeR9S.response_data = [
        SimpleNamespace(id="b", endpoints=["/v1/messages"], model_dump=lambda **_: {}),
        SimpleNamespace(id="a", endpoints=["/v1/messages", "/v1/responses"], model_dump=lambda **_: {}),
        SimpleNamespace(id="c", endpoints=["/v1/chat/completions"], model_dump=lambda **_: {}),
    ]
    monkeypatch.setattr(cli, "R9S", _FakeR9S)

    result = cli.fetch_models(
        "https://example.com/v1",
        "secret",
        timeout=7,
        endpoint_filter="/v1/messages",
    )

    assert result == ["a", "b"]
    assert _FakeR9S.calls == [
        {
            "api_key": "secret",
            "server_url": "https://example.com/v1",
            "timeout_ms": 7000,
            "expand": "endpoints",
            "filter": None,
        }
    ]


def test_fetch_models_uses_sdk_without_expand_when_no_endpoint_filter(monkeypatch) -> None:
    _FakeR9S.calls = []
    _FakeR9S.response_data = [
        SimpleNamespace(id="b", endpoints=None, model_dump=lambda **_: {}),
        SimpleNamespace(id="a", endpoints=None, model_dump=lambda **_: {}),
    ]
    monkeypatch.setattr(cli, "R9S", _FakeR9S)

    result = cli.fetch_models("https://example.com/v1", "secret")

    assert result == ["a", "b"]
    assert _FakeR9S.calls == [
        {
            "api_key": "secret",
            "server_url": "https://example.com/v1",
            "timeout_ms": 5000,
            "expand": None,
            "filter": None,
        }
    ]
