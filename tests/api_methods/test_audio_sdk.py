from __future__ import annotations

import pytest

from r9s import R9S


def test_audio_speech_includes_instructions_and_stream_format(
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

    monkeypatch.setattr("r9s.audio_sdk.utils.serialize_request_body", fake_serialize_request_body)
    monkeypatch.setattr("r9s.audio_sdk.AudioSDK.do_request", fake_do_request)

    client = R9S(api_key="test")

    with pytest.raises(RuntimeError, match="stop after capturing request"):
        client.audio.speech(
            model="gpt-4o-mini-tts",
            input="Hello world",
            voice="alloy",
            instructions="Speak warmly.",
            stream_format="sse",
        )

    request_body = captured["request_body"]
    assert request_body.instructions == "Speak warmly."
    assert request_body.stream_format == "sse"


def test_audio_transcribe_includes_diarization_fields(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured: dict[str, object] = {}

    def fake_serialize_request_body(request_body, *_args, **_kwargs):
        captured["request_body"] = request_body

        class _Body:
            media_type = "multipart/form-data"
            content = None
            data = {}
            files = []

        return _Body()

    def fake_do_request(self, **_kwargs):
        raise RuntimeError("stop after capturing request")

    monkeypatch.setattr("r9s.audio_sdk.utils.serialize_request_body", fake_serialize_request_body)
    monkeypatch.setattr("r9s.audio_sdk.AudioSDK.do_request", fake_do_request)

    client = R9S(api_key="test")

    with pytest.raises(RuntimeError, match="stop after capturing request"):
        client.audio.transcribe(
            file={"file_name": "meeting.wav", "content": b"audio-bytes"},
            model="gpt-4o-transcribe-diarize",
            chunking_strategy="auto",
            include=["logprobs"],
            known_speaker_names=["Alice", "Bob"],
            known_speaker_references=["data:audio/wav;base64,QUJD"],
            response_format="diarized_json",
            stream=True,
        )

    request_body = captured["request_body"]
    assert request_body.chunking_strategy == "auto"
    assert request_body.include == ["logprobs"]
    assert request_body.known_speaker_names == ["Alice", "Bob"]
    assert request_body.known_speaker_references == ["data:audio/wav;base64,QUJD"]
    assert request_body.stream is True


@pytest.mark.asyncio
async def test_audio_speech_async_includes_instructions_and_stream_format(
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

    async def fake_do_request_async(self, **_kwargs):
        raise RuntimeError("stop after capturing request")

    monkeypatch.setattr("r9s.audio_sdk.utils.serialize_request_body", fake_serialize_request_body)
    monkeypatch.setattr("r9s.audio_sdk.AudioSDK.do_request_async", fake_do_request_async)

    client = R9S(api_key="test")

    with pytest.raises(RuntimeError, match="stop after capturing request"):
        await client.audio.speech_async(
            model="gpt-4o-mini-tts",
            input="Hello async",
            voice="verse",
            instructions="Use a calm tone.",
            stream_format="audio",
        )

    request_body = captured["request_body"]
    assert request_body.instructions == "Use a calm tone."
    assert request_body.stream_format == "audio"
