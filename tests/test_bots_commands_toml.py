from __future__ import annotations

from r9s.cli_tools.bots import BotConfig, load_bot, save_bot
from r9s.cli_tools.commands import CommandConfig, load_command, save_command


def test_bot_toml_roundtrip(temp_home) -> None:
    bot = BotConfig(
        name="reviewer",
        description="desc",
        system_prompt="You are a bot.",
        temperature=0.2,
        top_p=0.9,
        max_tokens=123,
        presence_penalty=0.1,
        frequency_penalty=0.2,
    )
    path = save_bot(bot)
    assert path.exists()

    loaded = load_bot("reviewer")
    assert loaded.name == "reviewer"
    assert loaded.description == "desc"
    assert loaded.system_prompt == "You are a bot."
    assert loaded.temperature == 0.2
    assert loaded.top_p == 0.9
    assert loaded.max_tokens == 123
    assert loaded.presence_penalty == 0.1
    assert loaded.frequency_penalty == 0.2


def test_command_toml_roundtrip(temp_home) -> None:
    cmd = CommandConfig(name="summarize", description="desc", prompt="Say {{args}}")
    path = save_command(cmd)
    assert path.exists()

    loaded = load_command("summarize")
    assert loaded.name == "summarize"
    assert loaded.description == "desc"
    assert loaded.prompt == "Say {{args}}"
