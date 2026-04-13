from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Optional

try:
    import tomllib  # pyright: ignore[reportMissingImports]
except Exception:  # pragma: no cover
    tomllib = None  # type: ignore[assignment]

try:
    import tomli  # pyright: ignore[reportMissingImports]
except Exception:  # pragma: no cover
    tomli = None  # type: ignore[assignment]


def user_config_path() -> Path:
    return Path.home() / ".r9s" / "config.toml"


def _load_toml(path: Path) -> Dict[str, Any]:
    raw = path.read_bytes()
    if tomllib is not None:
        data = tomllib.loads(raw.decode("utf-8"))
    elif tomli is not None:
        data = tomli.loads(raw.decode("utf-8"))
    else:
        raise RuntimeError("TOML parser is not available (need tomllib or tomli)")
    if not isinstance(data, dict):
        raise ValueError(f"invalid toml file: {path}")
    return data


def read_user_config() -> Dict[str, Any]:
    path = user_config_path()
    if not path.exists():
        return {}
    try:
        return _load_toml(path)
    except Exception as exc:
        raise ValueError(f"failed to read user config {path}: {exc}") from exc


def get_user_config_string(key: str) -> Optional[str]:
    data = read_user_config()
    if key not in data:
        return None
    value = data[key]
    if value is None:
        return None
    if not isinstance(value, str):
        raise ValueError(
            f"failed to read user config {user_config_path()}: '{key}' must be a string"
        )
    value = value.strip()
    return value or None
