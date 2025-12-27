from __future__ import annotations

import argparse
from typing import Iterable

from r9s.cli_tools.bots import list_bots
from r9s.cli_tools.commands import list_commands
from r9s.cli_tools.tools.registry import (
    supported_app_names_for_config,
    supported_app_names_for_run,
)


def _bash_script() -> str:
    # This completion script is intentionally self-contained and does not depend on
    # bash-completion's _init_completion helper.
    return r"""# bash completion for r9s
# Usage:
#   eval "$(r9s completion bash)"

_r9s_completion() {
  local cur cword words
  cur="${COMP_WORDS[COMP_CWORD]}"
  # Drop the binary name.
  words=("${COMP_WORDS[@]:1}")
  cword=$((COMP_CWORD-1))
  if [ "$cword" -lt 0 ]; then
    cword=0
  fi

  local IFS=$'\n'
  local -a candidates
  mapfile -t candidates < <(r9s __complete bash "$cword" "${words[@]}" 2>/dev/null)

  COMPREPLY=()
  local cand
  for cand in "${candidates[@]}"; do
    [[ -z "$cur" || "$cand" == "$cur"* ]] && COMPREPLY+=("$cand")
  done
}

complete -F _r9s_completion r9s
"""


def handle_completion(args: argparse.Namespace) -> None:
    shell = (getattr(args, "shell", None) or "bash").strip().lower()
    if shell != "bash":
        raise SystemExit("Only bash is supported for now.")
    print(_bash_script(), end="")


def _complete_top_level() -> list[str]:
    # Keep in sync with cli.py subparsers.
    return ["chat", "bot", "command", "run", "set", "reset", "completion"]


def _complete_bot(words: list[str], cword: int, cur: str) -> list[str]:
    if cword == 1:
        return ["create", "list", "show", "delete"]
    if len(words) < 2:
        return []
    sub = words[1]
    if sub in ("show", "delete") and cword == 2 and not cur.startswith("-"):
        return list_bots()
    return []


def _complete_command(words: list[str], cword: int, cur: str) -> list[str]:
    if cword == 1:
        return ["create", "list", "show", "delete", "render", "run"]
    if len(words) < 2:
        return []
    sub = words[1]
    if sub in ("show", "delete", "render", "run") and cword == 2 and not cur.startswith(
        "-"
    ):
        return list_commands()
    return []


def _complete_chat(words: list[str], cword: int, cur: str) -> list[str]:
    if cword == 1 and not cur.startswith("-"):
        return list_bots()
    if cur.startswith("-"):
        return [
            "--lang",
            "--resume",
            "--api-key",
            "--base-url",
            "--model",
            "--system-prompt",
            "--history-file",
            "--no-history",
            "--ext",
            "--no-stream",
            "-y",
            "--yes",
        ]
    return []


def _complete_run(words: list[str], cword: int, cur: str) -> list[str]:
    if cword == 1 and not cur.startswith("-"):
        return supported_app_names_for_run()
    if cur.startswith("-"):
        return [
            "--api-key",
            "--base-url",
            "--model",
            "--print-env",
            "--confirm",
        ]
    return []


def _complete_set_reset(words: list[str], cword: int, cur: str) -> list[str]:
    if cword == 1 and not cur.startswith("-"):
        return supported_app_names_for_config()
    if cur.startswith("-"):
        return ["--lang", "--api-key", "--base-url", "--model"]
    return []


def _complete_completion(words: list[str], cword: int, cur: str) -> list[str]:
    if cword == 1 and not cur.startswith("-"):
        return ["bash", "zsh", "fish"]
    return []


def _filter_prefix(candidates: Iterable[str], prefix: str) -> list[str]:
    if not prefix:
        return sorted(set(candidates))
    return sorted({c for c in candidates if c.startswith(prefix)})


def compute_completions(shell: str, cword: int, words: list[str]) -> list[str]:
    shell = shell.strip().lower()
    if shell != "bash":
        return []

    if cword < 0:
        cword = 0
    cur = words[cword] if 0 <= cword < len(words) else ""

    # Global options (before any subcommand).
    if cword == 0 and cur.startswith("-"):
        return _filter_prefix(["--lang", "-h", "--help"], cur)

    if not words:
        return _filter_prefix(_complete_top_level(), cur)

    cmd = words[0]
    if cword == 0:
        return _filter_prefix(_complete_top_level(), cur)

    if cmd == "bot":
        return _filter_prefix(_complete_bot(words, cword, cur), cur)
    if cmd == "command":
        return _filter_prefix(_complete_command(words, cword, cur), cur)
    if cmd == "chat":
        return _filter_prefix(_complete_chat(words, cword, cur), cur)
    if cmd == "run":
        return _filter_prefix(_complete_run(words, cword, cur), cur)
    if cmd in ("set", "reset"):
        return _filter_prefix(_complete_set_reset(words, cword, cur), cur)
    if cmd == "completion":
        return _filter_prefix(_complete_completion(words, cword, cur), cur)

    return []


def handle___complete(args: argparse.Namespace) -> None:
    shell = (getattr(args, "shell", None) or "bash").strip().lower()
    cword = int(getattr(args, "cword", 0))
    words = list(getattr(args, "words", []) or [])
    # Avoid noisy failures during completion.
    try:
        out = compute_completions(shell, cword, words)
    except Exception:
        out = []
    print("\n".join(out))
