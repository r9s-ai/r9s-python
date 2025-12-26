from __future__ import annotations

from r9s.cli_tools.cli import build_parser


def test_chat_positional_bot_parses() -> None:
    parser = build_parser()

    args = parser.parse_args(["chat"])
    assert args.command == "chat"
    assert args.bot is None
    assert args.resume is False

    args = parser.parse_args(["chat", "reviewer"])
    assert args.command == "chat"
    assert args.bot == "reviewer"
    assert args.resume is False

    args = parser.parse_args(["chat", "--resume"])
    assert args.command == "chat"
    assert args.bot is None
    assert args.resume is True


def test_chat_yes_flag() -> None:
    parser = build_parser()
    args = parser.parse_args(["chat", "-y"])
    assert args.yes is True
