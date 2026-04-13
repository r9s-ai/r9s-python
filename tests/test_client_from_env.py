from __future__ import annotations

from pathlib import Path

import pytest

from r9s.client import R9S


def _write_user_config(home: Path, content: str) -> None:
    path = home / ".r9s" / "config.toml"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


class TestR9SFromEnv:
    def test_reads_api_key_and_base_url_from_config(
        self, temp_home: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.delenv("R9S_API_KEY", raising=False)
        monkeypatch.delenv("R9S_BASE_URL", raising=False)
        _write_user_config(
            temp_home,
            'api_key = "config-key"\nbase_url = "https://config.example/v1"\n',
        )

        client = R9S.from_env()

        assert client.sdk_configuration.security.api_key == "config-key"
        assert client.sdk_configuration.get_server_details()[0] == "https://config.example/v1"

    def test_env_overrides_config(
        self, temp_home: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setenv("R9S_API_KEY", "env-key")
        monkeypatch.setenv("R9S_BASE_URL", "https://env.example/v1")
        _write_user_config(
            temp_home,
            'api_key = "config-key"\nbase_url = "https://config.example/v1"\n',
        )

        client = R9S.from_env()

        assert client.sdk_configuration.security.api_key == "env-key"
        assert client.sdk_configuration.get_server_details()[0] == "https://env.example/v1"

    def test_uses_default_base_url_when_config_missing(
        self, temp_home: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.delenv("R9S_API_KEY", raising=False)
        monkeypatch.delenv("R9S_BASE_URL", raising=False)
        _write_user_config(temp_home, 'api_key = "config-key"\n')

        client = R9S.from_env(default_base_url="https://default.example/v1")

        assert client.sdk_configuration.get_server_details()[0] == "https://default.example/v1"

    def test_missing_api_key_raises(
        self, temp_home: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.delenv("R9S_API_KEY", raising=False)
        _write_user_config(temp_home, 'base_url = "https://config.example/v1"\n')

        with pytest.raises(
            ValueError,
            match=r"R9S_API_KEY is not set, and ~/.r9s/config\.toml does not define api_key\.",
        ):
            R9S.from_env()
