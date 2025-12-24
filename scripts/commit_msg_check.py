from __future__ import annotations

import re
import sys
from pathlib import Path


ALLOWED_TYPES = (
    "feat",
    "fix",
    "docs",
    "style",
    "refactor",
    "perf",
    "test",
    "build",
    "ci",
    "chore",
    "revert",
)

_CONVENTIONAL_RE = re.compile(
    rf"^({'|'.join(ALLOWED_TYPES)})(\\([^)]+\\))?(!)?: .+"
)


def main(argv: list[str]) -> int:
    if len(argv) < 2:
        print("usage: commit_msg_check.py <commit_msg_file>", file=sys.stderr)
        return 2

    path = Path(argv[1])
    try:
        msg = path.read_text(encoding="utf-8").strip()
    except FileNotFoundError:
        return 0

    if not msg:
        print("Empty commit message is not allowed.", file=sys.stderr)
        return 1

    first_line = msg.splitlines()[0].strip()

    # Allow auto-generated messages.
    if first_line.startswith("Merge "):
        return 0
    if first_line.startswith("Revert "):
        return 0

    if _CONVENTIONAL_RE.match(first_line):
        return 0

    allowed = ", ".join(ALLOWED_TYPES)
    print(
        "Invalid commit message format.\n\n"
        "Expected Conventional Commits:\n"
        "  <type>(<scope>)?: <description>\n"
        "  <type>!: <description>\n\n"
        f"Allowed types: {allowed}\n\n"
        "Examples:\n"
        "  feat(cli): add run command\n"
        "  fix(chat): handle missing finish_reason\n"
        "  docs: update README\n",
        file=sys.stderr,
    )
    return 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))

