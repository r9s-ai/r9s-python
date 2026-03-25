from __future__ import annotations

import argparse
from types import SimpleNamespace

import r9s.cli_tools.models_cli as models_cli


def test_models_details_table_includes_context_length_column(
    monkeypatch, capsys
) -> None:
    calls: list[dict[str, object]] = []

    class _FakeListResponse:
        def model_dump(self, **kwargs):
            assert kwargs == {"by_alias": True, "exclude_none": True}
            return {
                "object": "list",
                "data": [
                    {
                        "id": "a",
                        "owned_by": "x",
                        "created": 0,
                        "context_length": 8192,
                        "modality": "text->text",
                        "channels": ["OpenAI Official"],
                        "endpoints": ["/v1/chat/completions", "/v1/responses"],
                    },
                    {"id": "b", "owned_by": "y", "created": 0},
                ],
            }

    class _FakeR9S:
        def __init__(self, *, api_key: str, server_url: str):
            calls.append({"api_key": api_key, "server_url": server_url})
            self.models = SimpleNamespace(list=self._list)

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return None

        def _list(self, *, expand=None, filter=None):
            calls.append({"expand": expand, "filter": filter})
            return _FakeListResponse()

    monkeypatch.setattr(models_cli, "R9S", _FakeR9S)
    monkeypatch.setattr(models_cli, "_require_api_key", lambda preset, lang: "test-key")

    args = argparse.Namespace(
        lang="en",
        api_key="test-key",
        base_url="https://example.com/v1",
        expand="all",
        filter=None,
        details=True,
        verbose=False,
    )
    models_cli.handle_models_list(args)

    out = capsys.readouterr().out
    assert calls == [
        {"api_key": "test-key", "server_url": "https://example.com/v1"},
        {"expand": "all", "filter": None},
    ]
    assert "context_length" in out
    assert "modality" in out
    assert "channels" in out
    assert "endpoints" in out
    assert "8192" in out
    assert "text->text" in out
    assert "OpenAI Official" in out
    assert "/v1/chat/completions" in out


def test_models_verbose_uses_sdk_directly(monkeypatch, capsys) -> None:
    calls: list[dict[str, object]] = []

    class _FakeListResponse:
        def model_dump(self, **kwargs):
            assert kwargs == {"by_alias": True, "exclude_none": True}
            return {"object": "list", "data": [{"id": "a", "owned_by": "x", "created": 0}]}

    class _FakeR9S:
        def __init__(self, *, api_key: str, server_url: str):
            calls.append({"api_key": api_key, "server_url": server_url})
            self.models = SimpleNamespace(list=self._list)

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return None

        def _list(self, *, expand=None, filter=None):
            calls.append({"expand": expand, "filter": filter})
            return _FakeListResponse()

    monkeypatch.setattr(models_cli, "R9S", _FakeR9S)
    monkeypatch.setattr(models_cli, "_require_api_key", lambda preset, lang: "test-key")

    args = argparse.Namespace(
        lang="en",
        api_key="test-key",
        base_url="https://example.com/v1",
        expand=None,
        filter=["endpoint=/v1/messages"],
        details=False,
        verbose=True,
    )
    models_cli.handle_models_list(args)

    out = capsys.readouterr().out
    assert '"id": "a"' in out
    assert calls == [
        {"api_key": "test-key", "server_url": "https://example.com/v1"},
        {"expand": None, "filter": ["endpoint=/v1/messages"]},
    ]
