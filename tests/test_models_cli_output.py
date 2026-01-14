from __future__ import annotations

import argparse

import r9s.cli_tools.models_cli as models_cli


def test_models_details_table_includes_context_length_column(
    monkeypatch, capsys
) -> None:
    def _fake_request_models(*, api_key: str, base_url: str, expand: str | None, filters):
        assert api_key
        assert base_url
        assert expand == "all"
        assert filters is None
        return {
            "object": "list",
            "data": [
                {
                    "id": "a",
                    "owned_by": "x",
                    "created": 0,
                    "context_length": 8192,
                    "modality": "text->text",
                    "channels": ["OpenAI官方"],
                    "endpoints": ["/v1/chat/completions", "/v1/responses"],
                },
                {"id": "b", "owned_by": "y", "created": 0},
            ],
        }

    monkeypatch.setattr(models_cli, "_request_models", _fake_request_models)

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
    assert "context_length" in out
    assert "modality" in out
    assert "channels" in out
    assert "endpoints" in out
    assert "8192" in out
    assert "text->text" in out
    assert "OpenAI官方" in out
    assert "/v1/chat/completions" in out
