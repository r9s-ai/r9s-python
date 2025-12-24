from __future__ import annotations

import json
import os
import sys
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Tuple

import importlib.metadata


_PYPISIMPLE_JSON = "https://pypi.org/pypi/r9s/json"


@dataclass
class _Cache:
    checked_at: float
    latest: str
    current: str


def _cache_path() -> Path:
    return Path.home() / ".r9s" / "update-check.json"


def _read_cache() -> Optional[_Cache]:
    path = _cache_path()
    try:
        raw = path.read_text(encoding="utf-8")
    except FileNotFoundError:
        return None
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        return None
    if not isinstance(data, dict):
        return None
    try:
        return _Cache(
            checked_at=float(data.get("checked_at", 0.0)),
            latest=str(data.get("latest", "")),
            current=str(data.get("current", "")),
        )
    except Exception:
        return None


def _write_cache(cache: _Cache) -> None:
    path = _cache_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "checked_at": cache.checked_at,
        "latest": cache.latest,
        "current": cache.current,
    }
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )


def _parse_simple_version(value: str) -> Optional[Tuple[int, ...]]:
    # Best-effort parser for stable versions like "0.4.1".
    parts = value.strip().split(".")
    nums: list[int] = []
    for p in parts:
        head = ""
        for ch in p:
            if ch.isdigit():
                head += ch
            else:
                break
        if head == "":
            return None
        nums.append(int(head))
    return tuple(nums)


def _get_installed_version() -> Optional[str]:
    try:
        return importlib.metadata.version("r9s")
    except importlib.metadata.PackageNotFoundError:
        return None


def _fetch_latest_version(timeout_s: float = 1.5) -> Optional[str]:
    req = urllib.request.Request(
        _PYPISIMPLE_JSON,
        headers={"User-Agent": "r9s-cli-update-check"},
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout_s) as resp:
            payload = resp.read()
    except (urllib.error.URLError, TimeoutError):
        return None
    try:
        data = json.loads(payload.decode("utf-8"))
    except Exception:
        return None
    if isinstance(data, dict) and isinstance(data.get("info"), dict):
        v = data["info"].get("version")
        if isinstance(v, str) and v.strip():
            return v.strip()
    return None


def maybe_notify_update(*, interval_hours: float = 24.0) -> None:
    """Check PyPI for updates and print a notice (stderr) if a newer version exists.

    - Safe-by-default: network failures are ignored.
    - Cached: checks at most once per interval.
    - Quiet in non-interactive contexts: only notifies on TTY.
    """
    if os.getenv("R9S_NO_UPDATE_CHECK"):
        return

    # Avoid polluting scripted output.
    if not sys.stderr.isatty():
        return

    current = _get_installed_version()
    if not current:
        return

    now = time.time()
    cache = _read_cache()
    if (
        cache
        and (now - cache.checked_at) < (interval_hours * 3600.0)
        and cache.current == current
    ):
        latest = cache.latest
    else:
        latest = _fetch_latest_version()
        if not latest:
            return
        _write_cache(_Cache(checked_at=now, latest=latest, current=current))

    cur_v = _parse_simple_version(current)
    latest_v = _parse_simple_version(latest)
    if not cur_v or not latest_v:
        return
    if latest_v <= cur_v:
        return

    sys.stderr.write(
        f"Update available: r9s {current} -> {latest}. Run: pip install -U r9s\n"
    )
