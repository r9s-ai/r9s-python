from dataclasses import dataclass
from datetime import datetime
import shutil
from pathlib import Path
from typing import List, Optional


@dataclass
class ToolConfigSetResult:
    """Result returned by a tool integration after applying configuration."""

    target_path: Path
    backup_path: Optional[Path]


class ToolIntegration:
    """Base class that tool integrations can inherit from.

    It provides common behavior for:
    - managing backup files
    - restoring configuration from backups

    Concrete tools typically:
    - set `primary_name` and `aliases`
    - initialize `_settings_path` and `_backup_dir`
    - implement `set_config`
    """

    # Human/CLI identifier for the tool, e.g. "claude-code"
    primary_name: str

    # Additional names that should resolve to this tool, e.g. ["claude", "claude_code"]
    aliases: List[str]

    def set_config(self, *, base_url: str, api_key: str, model: str) -> ToolConfigSetResult:
        """Apply r9s configuration for this tool and return where it was written.

        Subclasses must implement this.
        """

        raise NotImplementedError

    # --- Common backup helpers -------------------------------------------------

    def list_backups(self) -> List[Path]:
        """Return all known backup files for this tool, ordered oldest → newest."""

        backup_dir = getattr(self, "_backup_dir", None)
        if backup_dir is None or not isinstance(backup_dir, Path):
            return []
        if not backup_dir.exists():
            return []
        return sorted([p for p in backup_dir.iterdir() if p.is_file()])

    def reset_config(self, backup_path: Path) -> Path:
        """Restore configuration from the given backup file."""

        settings_path = getattr(self, "_settings_path", None)
        if settings_path is None or not isinstance(settings_path, Path):
            raise SystemExit("ToolIntegration is missing _settings_path")
        if not backup_path.exists():
            raise SystemExit(f"Backup file does not exist: {backup_path}")
        settings_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(backup_path, settings_path)
        return settings_path

    def _create_backup_if_exists(self) -> Optional[Path]:
        """Create a timestamped backup of the current settings file if it exists."""

        settings_path = getattr(self, "_settings_path", None)
        backup_dir = getattr(self, "_backup_dir", None)
        if (
            settings_path is None
            or backup_dir is None
            or not isinstance(settings_path, Path)
            or not isinstance(backup_dir, Path)
        ):
            return None
        if not settings_path.exists():
            return None
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        backup_dir.mkdir(parents=True, exist_ok=True)
        backup_filename = settings_path.name
        backup_path = backup_dir / f"{backup_filename}.{timestamp}.bak"
        shutil.copy2(settings_path, backup_path)
        return backup_path
