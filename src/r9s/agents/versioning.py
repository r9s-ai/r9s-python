from __future__ import annotations

import re
from typing import Tuple

from r9s.agents.exceptions import InvalidVersionError


_VERSION_RE = re.compile(r"^(\d+)\.(\d+)\.(\d+)$")


def parse_version(value: str) -> Tuple[int, int, int]:
    match = _VERSION_RE.match(value.strip()) if value else None
    if not match:
        raise InvalidVersionError(f"Invalid version: {value}")
    return tuple(int(part) for part in match.groups())  # type: ignore[return-value]


def increment_version(value: str, bump: str = "patch") -> str:
    major, minor, patch = parse_version(value)
    if bump == "patch":
        patch += 1
    elif bump == "minor":
        minor += 1
        patch = 0
    elif bump == "major":
        major += 1
        minor = 0
        patch = 0
    else:
        raise InvalidVersionError(f"Invalid bump type: {bump}")
    return f"{major}.{minor}.{patch}"


def compare_versions(v1: str, v2: str) -> int:
    a = parse_version(v1)
    b = parse_version(v2)
    if a == b:
        return 0
    return -1 if a < b else 1
