from __future__ import annotations

from r9s.cli_tools.cli import build_parser


def test_skill_commands_parse() -> None:
    parser = build_parser()

    args = parser.parse_args(["skill", "list"])
    assert args.command == "skill"
    assert args.skill_command == "list"

    args = parser.parse_args(
        ["skill", "create", "code-review", "--description", "desc", "--instructions", "body"]
    )
    assert args.command == "skill"
    assert args.skill_command == "create"
    assert args.name == "code-review"

    args = parser.parse_args(["skill", "validate", "code-review", "--allow-scripts"])
    assert args.command == "skill"
    assert args.skill_command == "validate"
    assert args.allow_scripts is True
