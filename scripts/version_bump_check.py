from __future__ import annotations

import re
import subprocess
import sys
from typing import Optional, Tuple


_VERSION_RE = re.compile(r'^\s*version\s*=\s*"([^"]+)"\s*$', re.MULTILINE)


def _run_git(args: list[str]) -> Tuple[int, str]:
    proc = subprocess.run(
        ["git", *args],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        check=False,
    )
    return proc.returncode, proc.stdout


def _read_git_object(rev_path: str) -> Optional[str]:
    code, out = _run_git(["show", rev_path])
    if code != 0:
        return None
    return out


def _is_file_staged(path: str) -> bool:
    code, out = _run_git(["diff", "--cached", "--name-only", "--", path])
    return code == 0 and any(line.strip() == path for line in out.splitlines())


def _extract_version(pyproject_text: str) -> Optional[str]:
    m = _VERSION_RE.search(pyproject_text)
    if not m:
        return None
    return m.group(1).strip()


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


def main() -> int:
    path = "pyproject.toml"

    # Only enforce when pyproject.toml is part of the commit.
    if not _is_file_staged(path):
        return 0

    staged = _read_git_object(f":{path}")
    head = _read_git_object(f"HEAD:{path}")
    if staged is None or head is None:
        # Initial commit or unusual repo state: skip.
        return 0

    staged_v = _extract_version(staged)
    head_v = _extract_version(head)
    if not staged_v or not head_v:
        # If we cannot parse, do not block commits.
        return 0

    staged_t = _parse_simple_version(staged_v)
    head_t = _parse_simple_version(head_v)
    if staged_t is None or head_t is None:
        # Non-standard versions are ignored by this simple rule.
        return 0

    if staged_t <= head_t:
        print(
            "Version must be monotonically increasing.\n\n"
            f"Current (HEAD): {head_v}\n"
            f"Staged:         {staged_v}\n\n"
            "Please bump `project.version` in pyproject.toml before committing.",
            file=sys.stderr,
        )
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

