import json
from pathlib import Path

from .base import ToolConfigSetResult, ToolIntegration


class ClaudeCodeIntegration(ToolIntegration):
    primary_name = "claude-code"
    aliases = ["claude-code", "claude", "claude_code"]

    def __init__(self) -> None:
        self._settings_path = Path.home() / ".claude" / "settings.json"
        self._backup_dir = Path.home() / ".r9s" / "backup" / "claude-code"

    def set_config(
        self, *, base_url: str, api_key: str, model: str, small_model: str
    ) -> ToolConfigSetResult:
        # 标准化base_url：移除尾部斜杠和/v1后缀（Claude Code会自动添加API路径）
        normalized_base_url = base_url.rstrip("/")
        if normalized_base_url.endswith("/v1"):
            normalized_base_url = normalized_base_url[:-3]

        backup_path = self._create_backup_if_exists()
        data = self._read_settings()
        env = data.get("env")
        if not isinstance(env, dict):
            env = {}
        env.update(
            {
                "ANTHROPIC_BASE_URL": normalized_base_url,
                "ANTHROPIC_AUTH_TOKEN": api_key,
                "API_TIMEOUT_MS": "3000000",
                "CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC": 1,
                "ANTHROPIC_MODEL": model,
                "ANTHROPIC_SMALL_FAST_MODEL": small_model,
            }
        )
        data["env"] = env
        self._settings_path.parent.mkdir(parents=True, exist_ok=True)
        with self._settings_path.open("w", encoding="utf-8") as fp:
            json.dump(data, fp, indent=2, ensure_ascii=False)
            fp.write("\n")
        return ToolConfigSetResult(
            target_path=self._settings_path, backup_path=backup_path
        )

    def _read_settings(self) -> dict:
        if not self._settings_path.exists():
            return {}
        try:
            with self._settings_path.open("r", encoding="utf-8") as fp:
                data = json.load(fp)
        except (json.JSONDecodeError, OSError):
            return {}
        return data if isinstance(data, dict) else {}
