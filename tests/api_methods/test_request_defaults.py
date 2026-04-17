from __future__ import annotations

import pytest

from r9s import R9S


def _capture_request_body(
    monkeypatch: pytest.MonkeyPatch, module_path: str, sdk_path: str
) -> dict[str, object]:
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

    monkeypatch.setattr(f"{module_path}.utils.serialize_request_body", fake_serialize_request_body)
    monkeypatch.setattr(sdk_path, fake_do_request)
    return captured


def test_messages_omits_vendor_default_stream_and_service_tier(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured = _capture_request_body(
        monkeypatch,
        "r9s.messages",
        "r9s.messages.Messages.do_request",
    )

    client = R9S(api_key="test")

    with pytest.raises(RuntimeError, match="stop after capturing request"):
        client.messages.create(
            model="claude-sonnet-4.5",
            max_tokens=128,
            messages=[{"role": "user", "content": [{"type": "text", "text": "hi"}]}],
        )

    dumped = captured["request_body"].model_dump(by_alias=True, exclude_none=True)
    assert "stream" not in dumped
    assert "service_tier" not in dumped


def test_responses_omits_vendor_default_flags_and_truncation(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured = _capture_request_body(
        monkeypatch,
        "r9s.responses",
        "r9s.responses.Responses.do_request",
    )

    client = R9S(api_key="test")

    with pytest.raises(RuntimeError, match="stop after capturing request"):
        client.responses.create(
            model="gpt-4.1-mini",
            input="hello",
        )

    dumped = captured["request_body"].model_dump(by_alias=True, exclude_none=True)
    for key in [
        "stream",
        "parallel_tool_calls",
        "store",
        "background",
        "truncation",
    ]:
        assert key not in dumped


def test_completions_omits_vendor_sampling_defaults(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured = _capture_request_body(
        monkeypatch,
        "r9s.completions",
        "r9s.completions.Completions.do_request",
    )

    client = R9S(api_key="test")

    with pytest.raises(RuntimeError, match="stop after capturing request"):
        client.completions.create(
            model="gpt-3.5-turbo-instruct",
            prompt="hello",
        )

    dumped = captured["request_body"].model_dump(by_alias=True, exclude_none=True)
    for key in [
        "echo",
        "frequency_penalty",
        "n",
        "presence_penalty",
        "stream",
        "temperature",
        "top_p",
    ]:
        assert key not in dumped


def test_audio_speech_omits_vendor_audio_defaults(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured = _capture_request_body(
        monkeypatch,
        "r9s.audio_sdk",
        "r9s.audio_sdk.AudioSDK.do_request",
    )

    client = R9S(api_key="test")

    with pytest.raises(RuntimeError, match="stop after capturing request"):
        client.audio.speech(
            model="gpt-4o-mini-tts",
            input="hello",
            voice="alloy",
        )

    dumped = captured["request_body"].model_dump(by_alias=True, exclude_none=True)
    assert "response_format" not in dumped
    assert "speed" not in dumped


def test_moderations_omits_vendor_default_model(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured = _capture_request_body(
        monkeypatch,
        "r9s.moderations",
        "r9s.moderations.Moderations.do_request",
    )

    client = R9S(api_key="test")

    with pytest.raises(RuntimeError, match="stop after capturing request"):
        client.moderations.create(input="hello")

    dumped = captured["request_body"].model_dump(by_alias=True, exclude_none=True)
    assert "model" not in dumped


def test_chat_omits_vendor_default_stream(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured = _capture_request_body(
        monkeypatch,
        "r9s.chat",
        "r9s.chat.Chat.do_request",
    )

    client = R9S(api_key="test")

    with pytest.raises(RuntimeError, match="stop after capturing request"):
        client.chat.create(
            model="gpt-4.1-mini",
            messages=[{"role": "user", "content": "hello"}],
        )

    dumped = captured["request_body"].model_dump(by_alias=True, exclude_none=True)
    assert "stream" not in dumped


def test_edits_omits_vendor_defaults(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured = _capture_request_body(
        monkeypatch,
        "r9s.edits",
        "r9s.edits.Edits.do_request",
    )

    client = R9S(api_key="test")

    with pytest.raises(RuntimeError, match="stop after capturing request"):
        client.edits.create(
            model="text-davinci-edit-001",
            instruction="Fix grammar",
        )

    dumped = captured["request_body"].model_dump(by_alias=True, exclude_none=True)
    for key in ["input", "n", "temperature", "top_p"]:
        assert key not in dumped


def test_images_omits_vendor_defaults(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured = _capture_request_body(
        monkeypatch,
        "r9s.images",
        "r9s.images.Images.do_request",
    )

    client = R9S(api_key="test")

    with pytest.raises(RuntimeError, match="stop after capturing request"):
        client.images.edit(
            image={"file_name": "image.png", "content": b"png-bytes"},
            prompt="Add a hat",
        )

    dumped = captured["request_body"].model_dump(by_alias=True, exclude_none=True)
    for key in ["input_fidelity", "n", "partial_images", "size"]:
        assert key not in dumped
