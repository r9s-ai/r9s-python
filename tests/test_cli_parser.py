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

    args = parser.parse_args(["chat", "--agent", "support", "--var", "company=Acme"])
    assert args.command == "chat"
    assert args.agent == "support"
    assert args.var == ["company=Acme"]


def test_chat_yes_flag() -> None:
    parser = build_parser()
    args = parser.parse_args(["chat", "-y"])
    assert args.yes is True


def test_chat_allow_scripts_flag() -> None:
    parser = build_parser()
    args = parser.parse_args(["chat", "--allow-scripts"])
    assert args.allow_scripts is True


def test_models_expand_and_filter_parse() -> None:
    parser = build_parser()
    args = parser.parse_args(
        [
            "models",
            "--expand",
            "channels,modality,endpoints,context_length",
            "--filter",
            "channel=*open*",
            "--filter",
            "endpoint=/v1/messages",
            "-v",
        ]
    )
    assert args.command == "models"
    assert args.expand == "channels,modality,endpoints,context_length"
    assert args.filter == ["channel=*open*", "endpoint=/v1/messages"]
    assert args.verbose is True


def test_models_shortcuts_details_parse() -> None:
    parser = build_parser()

    args = parser.parse_args(["models", "-d"])
    assert args.command == "models"
    assert args.details is True
