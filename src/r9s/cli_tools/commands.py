from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

try:
    import tomllib  # pyright: ignore[reportMissingImports]
except Exception:  # pragma: no cover
    tomllib = None  # type: ignore[assignment]

try:
    import tomli  # pyright: ignore[reportMissingImports]
except Exception:  # pragma: no cover
    tomli = None  # type: ignore[assignment]


@dataclass
class CommandConfig:
    name: str
    description: Optional[str] = None
    prompt: Optional[str] = None


def commands_root() -> Path:
    return Path.home() / ".r9s" / "commands"


def command_path(name: str) -> Path:
    safe = name.strip()
    if not safe:
        raise ValueError("command name cannot be empty")
    return commands_root() / f"{safe}.toml"


def _load_toml(path: Path) -> Dict[str, Any]:
    raw = path.read_bytes()
    if tomllib is not None:
        data = tomllib.loads(raw.decode("utf-8"))
    elif tomli is not None:
        data = tomli.loads(raw.decode("utf-8"))
    else:
        raise RuntimeError("TOML parser is not available (need tomllib or tomli)")
    if not isinstance(data, dict):
        raise ValueError(f"invalid command config: {path}")
    return data


def _toml_quote(value: str) -> str:
    return json.dumps(value, ensure_ascii=False)


def _toml_multiline(value: str) -> str:
    if "'''" not in value:
        return "'''\n" + value + "\n'''"
    if '"""' not in value:
        return '"""\n' + value + '\n"""'
    return _toml_quote(value)


def _dump_command_toml(cmd: CommandConfig) -> str:
    lines: List[str] = []
    if cmd.description:
        lines.append(f"description = {_toml_quote(cmd.description)}")
    if cmd.prompt is not None:
        lines.append(f"prompt = {_toml_multiline(cmd.prompt)}")
    return "\n".join(lines).rstrip() + "\n"


def save_command(cmd: CommandConfig) -> Path:
    root = commands_root()
    root.mkdir(parents=True, exist_ok=True)
    path = command_path(cmd.name)
    path.write_text(_dump_command_toml(cmd), encoding="utf-8")
    return path


def load_command(name: str) -> CommandConfig:
    path = command_path(name)
    data = _load_toml(path)

    description_raw = data.get("description")
    description = (
        description_raw.strip()
        if isinstance(description_raw, str) and description_raw.strip()
        else None
    )

    prompt_raw = data.get("prompt")
    prompt = prompt_raw if isinstance(prompt_raw, str) else None
    prompt = prompt if (prompt and prompt.strip()) else None

    if not prompt:
        raise ValueError(f"command config missing 'prompt': {path}")

    return CommandConfig(name=name.strip(), description=description, prompt=prompt)


def list_commands() -> List[str]:
    root = commands_root()
    if not root.exists():
        return []
    return [p.stem for p in sorted(root.glob("*.toml"))]


def delete_command(name: str) -> Path:
    path = command_path(name)
    path.unlink()
    return path
