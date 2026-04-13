"""Tests for CLI config resolution with env/config precedence."""

from __future__ import annotations

from pathlib import Path

import pytest

from r9s.cli_tools.config import (
    get_api_key,
    resolve_base_url,
    resolve_image_model,
    resolve_model,
    resolve_stt_model,
    resolve_system_prompt,
    resolve_tts_model,
)


def _write_user_config(home: Path, content: str) -> None:
    path = home / ".r9s" / "config.toml"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


class TestResolveApiKey:
    def test_reads_from_config_when_env_and_args_missing(
        self, temp_home: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.delenv("R9S_API_KEY", raising=False)
        _write_user_config(temp_home, 'api_key = "config-key"\n')
        assert get_api_key(None) == "config-key"

    def test_env_overrides_config(
        self, temp_home: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setenv("R9S_API_KEY", "env-key")
        _write_user_config(temp_home, 'api_key = "config-key"\n')
        assert get_api_key(None) == "env-key"

    def test_args_override_env_and_config(
        self, temp_home: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setenv("R9S_API_KEY", "env-key")
        _write_user_config(temp_home, 'api_key = "config-key"\n')
        assert get_api_key("args-key") == "args-key"

    def test_strips_whitespace(
        self, temp_home: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.delenv("R9S_API_KEY", raising=False)
        _write_user_config(temp_home, 'api_key = "  config-key  "\n')
        assert get_api_key(None) == "config-key"


class TestResolveBaseUrl:
    def test_uses_default_when_no_sources(
        self, temp_home: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.delenv("R9S_BASE_URL", raising=False)
        assert resolve_base_url(None) == "https://api.r9s.ai/v1"

    def test_reads_from_config(
        self, temp_home: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.delenv("R9S_BASE_URL", raising=False)
        _write_user_config(temp_home, 'base_url = "https://config.example/v1"\n')
        assert resolve_base_url(None) == "https://config.example/v1"

    def test_env_overrides_config(
        self, temp_home: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setenv("R9S_BASE_URL", "https://env.example/v1")
        _write_user_config(temp_home, 'base_url = "https://config.example/v1"\n')
        assert resolve_base_url(None) == "https://env.example/v1"

    def test_args_override_env_and_config(
        self, temp_home: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setenv("R9S_BASE_URL", "https://env.example/v1")
        _write_user_config(temp_home, 'base_url = "https://config.example/v1"\n')
        assert resolve_base_url("https://args.example/v1") == "https://args.example/v1"


class TestResolveModel:
    def test_uses_default_when_no_sources(
        self, temp_home: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.delenv("R9S_MODEL", raising=False)
        assert resolve_model(None) == "gpt-5-nano"

    def test_reads_from_config(
        self, temp_home: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.delenv("R9S_MODEL", raising=False)
        _write_user_config(temp_home, 'model = "config-model"\n')
        assert resolve_model(None) == "config-model"

    def test_env_overrides_config(
        self, temp_home: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setenv("R9S_MODEL", "env-model")
        _write_user_config(temp_home, 'model = "config-model"\n')
        assert resolve_model(None) == "env-model"

    def test_args_override_env_and_config(
        self, temp_home: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setenv("R9S_MODEL", "env-model")
        _write_user_config(temp_home, 'model = "config-model"\n')
        assert resolve_model("args-model") == "args-model"


class TestResolveImageModel:
    def test_args_takes_priority(
        self, temp_home: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setenv("R9S_IMAGE_MODEL", "env-image-model")
        _write_user_config(temp_home, 'image_model = "config-image-model"\n')
        assert resolve_image_model("args-model") == "args-model"

    def test_image_env_over_config(
        self, temp_home: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setenv("R9S_IMAGE_MODEL", "env-image-model")
        _write_user_config(
            temp_home,
            'image_model = "config-image-model"\nmodel = "config-model"\n',
        )
        assert resolve_image_model(None) == "env-image-model"

    def test_config_over_default(
        self, temp_home: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.delenv("R9S_IMAGE_MODEL", raising=False)
        _write_user_config(
            temp_home,
            'image_model = "config-image-model"\nmodel = "config-model"\n',
        )
        assert resolve_image_model(None) == "config-image-model"

    def test_ignores_general_model_uses_default(
        self, temp_home: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.delenv("R9S_IMAGE_MODEL", raising=False)
        monkeypatch.delenv("R9S_MODEL", raising=False)
        _write_user_config(temp_home, 'model = "config-model"\n')
        assert resolve_image_model(None) == "gpt-image-1.5"

    def test_custom_default(
        self, temp_home: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.delenv("R9S_IMAGE_MODEL", raising=False)
        assert resolve_image_model(None, default="custom-default") == "custom-default"

    def test_strips_whitespace(
        self, temp_home: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.delenv("R9S_IMAGE_MODEL", raising=False)
        _write_user_config(temp_home, 'image_model = "  spaced-model  "\n')
        assert resolve_image_model(None) == "spaced-model"


class TestResolveTtsModel:
    def test_args_takes_priority(
        self, temp_home: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setenv("R9S_TTS_MODEL", "env-tts-model")
        _write_user_config(temp_home, 'tts_model = "config-tts-model"\n')
        assert resolve_tts_model("args-model") == "args-model"

    def test_env_fallback(
        self, temp_home: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setenv("R9S_TTS_MODEL", "env-tts-model")
        _write_user_config(temp_home, 'tts_model = "config-tts-model"\n')
        assert resolve_tts_model(None) == "env-tts-model"

    def test_config_fallback(
        self, temp_home: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.delenv("R9S_TTS_MODEL", raising=False)
        _write_user_config(temp_home, 'tts_model = "config-tts-model"\n')
        assert resolve_tts_model(None) == "config-tts-model"

    def test_custom_default(
        self, temp_home: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.delenv("R9S_TTS_MODEL", raising=False)
        assert resolve_tts_model(None, default="tts-1-hd") == "tts-1-hd"


class TestResolveSttModel:
    def test_args_takes_priority(
        self, temp_home: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setenv("R9S_STT_MODEL", "env-stt-model")
        _write_user_config(temp_home, 'stt_model = "config-stt-model"\n')
        assert resolve_stt_model("args-model") == "args-model"

    def test_env_fallback(
        self, temp_home: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setenv("R9S_STT_MODEL", "env-stt-model")
        _write_user_config(temp_home, 'stt_model = "config-stt-model"\n')
        assert resolve_stt_model(None) == "env-stt-model"

    def test_config_fallback(
        self, temp_home: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.delenv("R9S_STT_MODEL", raising=False)
        _write_user_config(temp_home, 'stt_model = "config-stt-model"\n')
        assert resolve_stt_model(None) == "config-stt-model"

    def test_custom_default(
        self, temp_home: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.delenv("R9S_STT_MODEL", raising=False)
        assert (
            resolve_stt_model(None, default="whisper-large-v3")
            == "whisper-large-v3"
        )


class TestResolveSystemPrompt:
    def test_returns_none_when_missing(
        self, temp_home: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.delenv("R9S_SYSTEM_PROMPT", raising=False)
        assert resolve_system_prompt(None) is None

    def test_reads_from_config(
        self, temp_home: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.delenv("R9S_SYSTEM_PROMPT", raising=False)
        _write_user_config(temp_home, 'system_prompt = "be helpful"\n')
        assert resolve_system_prompt(None) == "be helpful"

    def test_empty_config_value_is_treated_as_missing(
        self, temp_home: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.delenv("R9S_SYSTEM_PROMPT", raising=False)
        _write_user_config(temp_home, 'system_prompt = "   "\n')
        assert resolve_system_prompt(None) is None

    def test_env_overrides_config(
        self, temp_home: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setenv("R9S_SYSTEM_PROMPT", "env prompt")
        _write_user_config(temp_home, 'system_prompt = "config prompt"\n')
        assert resolve_system_prompt(None) == "env prompt"

    def test_args_override_env_and_config(
        self, temp_home: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setenv("R9S_SYSTEM_PROMPT", "env prompt")
        _write_user_config(temp_home, 'system_prompt = "config prompt"\n')
        assert resolve_system_prompt("args prompt") == "args prompt"


class TestConfigErrors:
    def test_invalid_toml_raises(
        self, temp_home: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.delenv("R9S_API_KEY", raising=False)
        _write_user_config(temp_home, 'api_key = "unterminated\n')
        with pytest.raises(ValueError, match=r"failed to read user config .*config\.toml"):
            get_api_key(None)

    def test_invalid_value_type_raises(
        self, temp_home: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.delenv("R9S_MODEL", raising=False)
        _write_user_config(temp_home, "model = 123\n")
        with pytest.raises(ValueError, match=r"'model' must be a string"):
            resolve_model(None)
