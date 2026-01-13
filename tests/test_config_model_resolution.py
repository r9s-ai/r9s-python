"""Tests for model resolution functions in config.py."""

from __future__ import annotations

import pytest

from r9s.cli_tools.config import (
    resolve_image_model,
    resolve_tts_model,
    resolve_stt_model,
)


class TestResolveImageModel:
    """Tests for resolve_image_model function."""

    def test_args_takes_priority(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("R9S_IMAGE_MODEL", "env-image-model")
        monkeypatch.setenv("R9S_MODEL", "env-model")
        assert resolve_image_model("args-model") == "args-model"

    def test_image_env_over_general_env(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("R9S_IMAGE_MODEL", "env-image-model")
        monkeypatch.setenv("R9S_MODEL", "env-model")
        assert resolve_image_model(None) == "env-image-model"

    def test_ignores_general_env_uses_default(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """R9S_MODEL is ignored since chat models are not valid for images."""
        monkeypatch.delenv("R9S_IMAGE_MODEL", raising=False)
        monkeypatch.setenv("R9S_MODEL", "env-model")
        assert resolve_image_model(None) == "gpt-image-1.5"

    def test_default_fallback(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.delenv("R9S_IMAGE_MODEL", raising=False)
        monkeypatch.delenv("R9S_MODEL", raising=False)
        assert resolve_image_model(None) == "gpt-image-1.5"

    def test_custom_default(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.delenv("R9S_IMAGE_MODEL", raising=False)
        monkeypatch.delenv("R9S_MODEL", raising=False)
        assert resolve_image_model(None, default="custom-default") == "custom-default"

    def test_strips_whitespace(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("R9S_IMAGE_MODEL", "  spaced-model  ")
        assert resolve_image_model(None) == "spaced-model"


class TestResolveTtsModel:
    """Tests for resolve_tts_model function."""

    def test_args_takes_priority(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("R9S_TTS_MODEL", "env-tts-model")
        assert resolve_tts_model("args-model") == "args-model"

    def test_env_fallback(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("R9S_TTS_MODEL", "env-tts-model")
        assert resolve_tts_model(None) == "env-tts-model"

    def test_default_fallback(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.delenv("R9S_TTS_MODEL", raising=False)
        assert resolve_tts_model(None) == "tts-1"

    def test_custom_default(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.delenv("R9S_TTS_MODEL", raising=False)
        assert resolve_tts_model(None, default="tts-1-hd") == "tts-1-hd"


class TestResolveSttModel:
    """Tests for resolve_stt_model function."""

    def test_args_takes_priority(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("R9S_STT_MODEL", "env-stt-model")
        assert resolve_stt_model("args-model") == "args-model"

    def test_env_fallback(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("R9S_STT_MODEL", "env-stt-model")
        assert resolve_stt_model(None) == "env-stt-model"

    def test_default_fallback(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.delenv("R9S_STT_MODEL", raising=False)
        assert resolve_stt_model(None) == "whisper-1"

    def test_custom_default(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.delenv("R9S_STT_MODEL", raising=False)
        assert resolve_stt_model(None, default="whisper-large-v3") == "whisper-large-v3"
