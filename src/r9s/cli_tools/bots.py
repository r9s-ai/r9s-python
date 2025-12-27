from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence

try:
    import tomllib  # pyright: ignore[reportMissingImports]
except Exception:  # pragma: no cover
    tomllib = None  # type: ignore[assignment]

try:
    import tomli  # pyright: ignore[reportMissingImports]
except Exception:  # pragma: no cover
    tomli = None  # type: ignore[assignment]


@dataclass
class BotConfig:
    name: str
    description: Optional[str] = None
    system_prompt: Optional[str] = None
    temperature: Optional[float] = None
    top_p: Optional[float] = None
    max_tokens: Optional[int] = None
    presence_penalty: Optional[float] = None
    frequency_penalty: Optional[float] = None


def bots_root() -> Path:
    return Path.home() / ".r9s" / "bots"


def bot_path(name: str) -> Path:
    safe = name.strip()
    if not safe:
        raise ValueError("bot name cannot be empty")
    return bots_root() / f"{safe}.toml"


def _load_toml(path: Path) -> Dict[str, Any]:
    raw = path.read_bytes()
    if tomllib is not None:
        data = tomllib.loads(raw.decode("utf-8"))
    elif tomli is not None:
        data = tomli.loads(raw.decode("utf-8"))
    else:
        raise RuntimeError("TOML parser is not available (need tomllib or tomli)")
    if not isinstance(data, dict):
        raise ValueError(f"invalid bot config: {path}")
    return data


def _toml_quote(value: str) -> str:
    return json.dumps(value, ensure_ascii=False)


def _toml_multiline(value: str) -> str:
    # Prefer literal multiline for readability; fall back when delimiter conflicts.
    if "'''" not in value:
        return "'''\n" + value + "\n'''"
    if '"""' not in value:
        return '"""\n' + value + '\n"""'
    return _toml_quote(value)


def _toml_format_array(items: Sequence[str]) -> str:
    return json.dumps(list(items), ensure_ascii=False)


def _dump_bot_toml(bot: BotConfig) -> str:
    lines: List[str] = []
    if bot.description:
        lines.append(f"description = {_toml_quote(bot.description)}")
    if bot.system_prompt is not None:
        lines.append(f"system_prompt = {_toml_multiline(bot.system_prompt)}")
    if bot.temperature is not None:
        lines.append(f"temperature = {bot.temperature}")
    if bot.top_p is not None:
        lines.append(f"top_p = {bot.top_p}")
    if bot.max_tokens is not None:
        lines.append(f"max_tokens = {bot.max_tokens}")
    if bot.presence_penalty is not None:
        lines.append(f"presence_penalty = {bot.presence_penalty}")
    if bot.frequency_penalty is not None:
        lines.append(f"frequency_penalty = {bot.frequency_penalty}")
    return "\n".join(lines).rstrip() + "\n"


def save_bot(bot: BotConfig) -> Path:
    root = bots_root()
    root.mkdir(parents=True, exist_ok=True)
    path = bot_path(bot.name)
    path.write_text(_dump_bot_toml(bot), encoding="utf-8")
    return path


def load_bot(name: str) -> BotConfig:
    path = bot_path(name)
    data = _load_toml(path)

    description_raw = data.get("description")
    description = (
        description_raw.strip()
        if isinstance(description_raw, str) and description_raw.strip()
        else None
    )

    system_prompt = (
        str(data["system_prompt"])
        if isinstance(data.get("system_prompt"), str)
        else None
    )
    system_prompt = (
        system_prompt.strip() if (system_prompt and system_prompt.strip()) else None
    )

    temperature = data.get("temperature")
    temperature = (
        float(temperature)
        if isinstance(temperature, (int, float)) and temperature is not None
        else None
    )

    top_p = data.get("top_p")
    top_p = (
        float(top_p) if isinstance(top_p, (int, float)) and top_p is not None else None
    )

    max_tokens = data.get("max_tokens")
    max_tokens = int(max_tokens) if isinstance(max_tokens, int) else None

    presence_penalty = data.get("presence_penalty")
    presence_penalty = (
        float(presence_penalty)
        if isinstance(presence_penalty, (int, float)) and presence_penalty is not None
        else None
    )

    frequency_penalty = data.get("frequency_penalty")
    frequency_penalty = (
        float(frequency_penalty)
        if isinstance(frequency_penalty, (int, float)) and frequency_penalty is not None
        else None
    )

    return BotConfig(
        name=name.strip(),
        description=description,
        system_prompt=system_prompt,
        temperature=temperature,
        top_p=top_p,
        max_tokens=max_tokens,
        presence_penalty=presence_penalty,
        frequency_penalty=frequency_penalty,
    )


def list_bots() -> List[str]:
    root = bots_root()
    if not root.exists():
        return []
    out: List[str] = []
    for p in sorted(root.glob("*.toml")):
        out.append(p.stem)
    return out


def delete_bot(name: str) -> Path:
    path = bot_path(name)
    path.unlink()
    return path
