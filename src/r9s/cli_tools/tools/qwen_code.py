import json
from pathlib import Path
from typing import Optional

from .base import ToolConfigSetResult, ToolIntegration


class QwenCodeIntegration(ToolIntegration):
    primary_name = "qwen-code"
    aliases = ["qwen-code", "qwen", "qwencode"]

    def __init__(self) -> None:
        self._settings_path = Path.home() / ".qwen" / "settings.json"
        self._env_path = Path.home() / ".qwen" / ".env"
        self._backup_dir = Path.home() / ".r9s" / "backup" / "qwen-code"

    def set_config(
        self,
        *,
        base_url: str,
        api_key: str,
        model: str,
        small_model: str,
        wire_api: str = "responses",
        reasoning_effort: str | None = None,
    ) -> ToolConfigSetResult:
        """Configure Qwen Code to use r9s API.

        Args:
            base_url: API base URL
            api_key: Authentication token
            model: Primary model name
            small_model: Not used for Qwen Code (kept for interface compatibility)
        """
        # Normalize base_url: remove trailing slash
        normalized_base_url = base_url.rstrip("/")

        # Create backup if config exists
        backup_path = self._create_backup_if_exists()

        # Write .env file
        self._write_env_file(normalized_base_url, api_key, model)

        # Update settings.json
        self._update_settings_json(model)

        return ToolConfigSetResult(
            target_path=self._settings_path, backup_path=backup_path
        )

    def _write_env_file(self, base_url: str, api_key: str, model: str) -> None:
        """Write environment variables to ~/.qwen/.env file."""
        env_content = f"""OPENAI_API_KEY={api_key}
OPENAI_BASE_URL={base_url}
OPENAI_MODEL={model}
"""
        self._env_path.parent.mkdir(parents=True, exist_ok=True)
        self._env_path.write_text(env_content, encoding="utf-8")

    def _update_settings_json(self, model: str) -> None:
        """Update settings.json with model configuration."""
        data = self._read_settings()

        # Configure authentication to use OpenAI-compatible API
        if "security" not in data:
            data["security"] = {}
        if "auth" not in data["security"]:
            data["security"]["auth"] = {}

        data["security"]["auth"] = {
            "selectedType": "openai",
            "apiKey": "$OPENAI_API_KEY",
            "baseUrl": "$OPENAI_BASE_URL",
        }

        # Ensure model section exists
        if "model" not in data:
            data["model"] = {}

        # Set model name to reference environment variable
        data["model"]["name"] = "$OPENAI_MODEL"

        # Set version if not present
        if "$version" not in data:
            data["$version"] = 2

        # Write settings file
        self._settings_path.parent.mkdir(parents=True, exist_ok=True)
        with self._settings_path.open("w", encoding="utf-8") as fp:
            json.dump(data, fp, indent=2, ensure_ascii=False)
            fp.write("\n")

    def _read_settings(self) -> dict:
        """Read existing settings.json or return empty dict."""
        if not self._settings_path.exists():
            return {}
        try:
            with self._settings_path.open("r", encoding="utf-8") as fp:
                data = json.load(fp)
        except (json.JSONDecodeError, OSError):
            return {}
        return data if isinstance(data, dict) else {}

    def _create_backup_if_exists(self) -> Optional[Path]:
        """Create timestamped backup of both .env and settings.json if they exist."""
        from datetime import datetime
        import shutil

        # Check if either file exists
        has_settings = self._settings_path.exists()
        has_env = self._env_path.exists()

        if not has_settings and not has_env:
            return None

        timestamp = datetime.now().strftime("%Y_%m_%d_%H%M%S")
        self._backup_dir.mkdir(parents=True, exist_ok=True)

        # Backup settings.json
        if has_settings:
            backup_settings = self._backup_dir / f"settings.json.{timestamp}.bak"
            shutil.copy2(self._settings_path, backup_settings)

        # Backup .env
        if has_env:
            backup_env = self._backup_dir / f".env.{timestamp}.bak"
            shutil.copy2(self._env_path, backup_env)

        # Return the backup directory as reference
        return self._backup_dir

    def list_backups(self) -> list[Path]:
        """Return all known backup files for this tool, ordered oldest → newest."""
        if not self._backup_dir.exists():
            return []
        # Only list settings.json backups for consistency with other tools
        backups = sorted(
            [
                p
                for p in self._backup_dir.iterdir()
                if p.name.startswith("settings.json")
            ]
        )
        return backups

    def reset_config(self, backup_path: Path) -> Path:
        """Restore configuration from the given backup file."""
        import shutil

        if not backup_path.exists():
            raise SystemExit(f"Backup file does not exist: {backup_path}")

        # Extract timestamp from backup filename (e.g., settings.json.20231225120000.bak)
        timestamp = backup_path.stem.split(".")[-1]

        # Restore settings.json
        if backup_path.name.startswith("settings.json"):
            self._settings_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(backup_path, self._settings_path)

            # Try to restore corresponding .env file
            env_backup = self._backup_dir / f".env.{timestamp}.bak"
            if env_backup.exists():
                shutil.copy2(env_backup, self._env_path)

        return self._settings_path

    def run_executable(self) -> str:
        """Return the executable name for running qwen-code."""
        return "qwen"

    def run_env(self, *, api_key: str, base_url: str, model: str) -> dict[str, str]:
        """Return environment variables for running qwen-code.

        Maps R9S configuration to OpenAI-compatible environment variables
        that qwen-code expects.
        """
        return {
            "OPENAI_API_KEY": api_key,
            "OPENAI_BASE_URL": base_url,
            "OPENAI_MODEL": model,
        }

    def run_args(self, *, base_url: str, model: str) -> list[str]:
        """Return additional command line arguments for running qwen-code.

        qwen-code reads configuration from environment variables,
        so no additional CLI arguments are needed.
        """
        return []
