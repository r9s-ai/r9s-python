import sys
from pathlib import Path
from typing import Optional

# Python 3.11+ has tomllib built-in
if sys.version_info >= (3, 11):
    import tomllib
else:
    try:
        import tomli as tomllib  # pyright: ignore[reportMissingImports]
    except ImportError:
        tomllib = None  # type: ignore[assignment]

try:
    import tomli_w  # pyright: ignore[reportMissingImports]
except ImportError:
    tomli_w = None  # type: ignore[assignment]

from .base import ToolConfigSetResult, ToolIntegration


class CodexIntegration(ToolIntegration):
    primary_name = "codex"
    aliases = ["codex", "openai-codex"]

    def __init__(self) -> None:
        self._settings_path = Path.home() / ".codex" / "config.toml"
        self._backup_dir = Path.home() / ".r9s" / "backup" / "codex"

    def set_config(
        self,
        *,
        base_url: str,
        api_key: str,
        model: str,
        small_model: str,
        wire_api: str = "responses",
        reasoning_effort: Optional[str] = None,
    ) -> ToolConfigSetResult:
        """Configure Codex to use r9s API.

        Args:
            base_url: API base URL
            api_key: Authentication token
            model: Primary model name
            small_model: Not used for Codex (kept for interface compatibility)
            wire_api: API protocol type (responses/chat/completion)
            reasoning_effort: Optional reasoning effort level (low/medium/high)
        """
        if tomllib is None or tomli_w is None:
            raise SystemExit(
                "Missing TOML dependencies. Install with: pip install tomli tomli-w"
            )

        # Normalize base_url: remove trailing slash and /v1 suffix
        normalized_base_url = base_url.rstrip("/")
        # if normalized_base_url.endswith("/v1"):
        #     normalized_base_url = normalized_base_url[:-3]

        # Create backup if config exists
        backup_path = self._create_backup_if_exists()

        # Read existing config or start fresh
        data = self._read_config()

        # Set top-level model configuration
        data["model"] = model
        data["model_provider"] = "r9s"

        # Set reasoning effort if specified
        if reasoning_effort:
            data["model_reasoning_effort"] = reasoning_effort
        elif "model_reasoning_effort" in data:
            # Remove it if not specified (model might not support it)
            del data["model_reasoning_effort"]

        # Ensure model_providers section exists
        if "model_providers" not in data:
            data["model_providers"] = {}

        # Configure r9s provider
        data["model_providers"]["r9s"] = {
            "name": "R9S",
            "base_url": normalized_base_url,
            "env_key": "R9S_API_KEY",
            "wire_api": wire_api,
        }

        # Note: API key should be set as environment variable
        # Codex reads from system environment, not from config file's [env] section

        # Write config file
        self._settings_path.parent.mkdir(parents=True, exist_ok=True)
        with self._settings_path.open("wb") as fp:
            tomli_w.dump(data, fp)

        return ToolConfigSetResult(
            target_path=self._settings_path, backup_path=backup_path
        )

    def run_executable(self) -> str:
        return "codex"

    def run_env(self, *, api_key: str, base_url: str, model: str) -> dict[str, str]:
        """Return environment variables for running Codex.

        Codex reads API key from the R9S_API_KEY environment variable
        which should already be set by the user (validated by run_cli.py).
        All other configs are passed via --config command line flags.
        """
        return {}

    def run_args(self, *, base_url: str, model: str) -> list[str]:
        """Return additional command line arguments for running Codex.

        Uses --config flags to temporarily create a r9s_temp provider
        that overrides config.toml settings without modifying the file.
        """
        provider_name = "r9s_temp"
        env_key = "R9S_API_KEY"
        wire_api = "responses"

        return [
            "--config", f"model_provider={provider_name}",
            "--config", f"model={model}",
            "--config", f"model_providers.{provider_name}.name={provider_name}",
            "--config", f"model_providers.{provider_name}.base_url={base_url}",
            "--config", f"model_providers.{provider_name}.env_key={env_key}",
            "--config", f"model_providers.{provider_name}.wire_api={wire_api}",
        ]

    def _read_config(self) -> dict:
        """Read existing TOML config or return empty dict."""
        if not self._settings_path.exists():
            return {}
        try:
            with self._settings_path.open("rb") as fp:
                data = tomllib.load(fp)
        except Exception:
            return {}
        return data if isinstance(data, dict) else {}
