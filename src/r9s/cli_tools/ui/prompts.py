from __future__ import annotations

import shutil
from typing import List

from r9s.cli_tools.ui.terminal import FG_CYAN, _style, error, prompt_text


def print_options_multi_column(options: List[str], columns: int = 2) -> None:
    """Print numbered options in multiple columns, adjusting to terminal width."""
    if not options:
        return
    if len(options) <= 5:
        max_num_width = len(f"{len(options)})")
        for idx, value in enumerate(options, start=1):
            num_str = f"{idx})"
            print(_style(num_str.rjust(max_num_width), FG_CYAN), value)
        return

    try:
        term_width = shutil.get_terminal_size().columns
    except Exception:
        term_width = 80

    max_num_width = len(f"{len(options)})")
    max_option_width = max(len(opt) for opt in options)
    column_width = max_num_width + 2 + max_option_width + 4
    max_columns = max(1, term_width // column_width)
    columns = min(columns, max_columns)
    rows = (len(options) + columns - 1) // columns

    for row in range(rows):
        line_parts: List[str] = []
        for col in range(columns):
            idx = col * rows + row
            if idx < len(options):
                num_str = f"{idx + 1})"
                formatted = (
                    f"{_style(num_str.rjust(max_num_width), FG_CYAN)} {options[idx]}"
                )
                if col < columns - 1:
                    display_len = max_num_width + 1 + len(options[idx])
                    padding = column_width - display_len
                    formatted += " " * padding
                line_parts.append(formatted)
        print("".join(line_parts))


def prompt_choice(prompt: str, options: List[str], show_options: bool = True) -> str:
    if show_options:
        print_options_multi_column(options, columns=3)
    while True:
        selection = prompt_text(f"{prompt} (enter number): ")
        if not selection.isdigit():
            error("Please enter a valid number.")
            continue
        num = int(selection)
        if 1 <= num <= len(options):
            return options[num - 1]
        error("Selection out of range, try again.")


def prompt_yes_no(prompt: str, default_no: bool = True) -> bool:
    suffix = "[y/N]" if default_no else "[Y/n]"
    answer = prompt_text(f"{prompt} {suffix}: ").lower()
    if not answer:
        return not default_no
    return answer in ("y", "yes")
