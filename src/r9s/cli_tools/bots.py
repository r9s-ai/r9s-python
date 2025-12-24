from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import List, Optional


@dataclass
class BotConfig:
    name: str
    model: str
    base_url: Optional[str] = None
    system_prompt: Optional[str] = None
    system_prompt_file: Optional[str] = None
    lang: Optional[str] = None
    extensions: Optional[List[str]] = None


def bots_root() -> Path:
    return Path.home() / ".r9s" / "bots"


def bot_path(name: str) -> Path:
    safe = name.strip()
    if not safe:
        raise ValueError("bot name cannot be empty")
    return bots_root() / f"{safe}.json"


def save_bot(bot: BotConfig) -> Path:
    root = bots_root()
    root.mkdir(parents=True, exist_ok=True)
    path = bot_path(bot.name)
    path.write_text(
        json.dumps(asdict(bot), ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    return path


def load_bot(name: str) -> BotConfig:
    path = bot_path(name)
    raw = path.read_text(encoding="utf-8")
    data = json.loads(raw)
    if not isinstance(data, dict):
        raise ValueError(f"invalid bot config: {path}")
    model = data.get("model")
    if not isinstance(model, str) or not model.strip():
        raise ValueError(f"bot config missing 'model': {path}")
    return BotConfig(
        name=str(data.get("name") or name),
        model=model.strip(),
        base_url=(
            str(data["base_url"]).strip()
            if isinstance(data.get("base_url"), str) and data.get("base_url")
            else None
        ),
        system_prompt=(
            str(data["system_prompt"])
            if isinstance(data.get("system_prompt"), str) and data.get("system_prompt")
            else None
        ),
        system_prompt_file=(
            str(data["system_prompt_file"]).strip()
            if isinstance(data.get("system_prompt_file"), str)
            and data.get("system_prompt_file")
            else None
        ),
        lang=(
            str(data["lang"]).strip()
            if isinstance(data.get("lang"), str) and data.get("lang")
            else None
        ),
        extensions=list(data["extensions"])
        if isinstance(data.get("extensions"), list)
        and all(isinstance(x, str) for x in data["extensions"])
        else None,
    )


def list_bots() -> List[str]:
    root = bots_root()
    if not root.exists():
        return []
    out: List[str] = []
    for p in sorted(root.glob("*.json")):
        out.append(p.stem)
    return out


def delete_bot(name: str) -> Path:
    path = bot_path(name)
    path.unlink()
    return path
