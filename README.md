# r9s

The official Python SDK and CLI for the r9s API.

## Quick start

Install:

```bash
pip install r9s
```

Or directly execute the CLI:

```bash
uvx r9s
```

Set your API key:

```bash
export R9S_API_KEY="your_api_key"
```

## CLI usage

Chat (interactive, streaming by default):

```bash
r9s chat
```

Chat (stdin, useful for scripts/pipes):

```bash
echo "hello" | r9s chat
```

Resume a saved chat session (interactive selection):

```bash
r9s chat resume
```

Bots (saved as TOML under `~/.r9s/bots/<name>.toml`, system prompt only):

```bash
r9s bot create reviewer --system-prompt "You are a helpful assistant"
r9s chat --bot reviewer
```

Commands (saved as TOML under `~/.r9s/commands/<name>.toml`, prompt template only):

```bash
r9s command create summarize --prompt "Summarize: {{args}}"
```

In interactive chat, commands are available as slash commands:

- `/summarize hello world`

Command templates:

- `{{args}}` is replaced by the slash command arguments.
- `!{...}` runs a local shell command (`bash -lc ...`) after confirmation; pass `-y` to skip confirmation.

Run apps with r9s env injected (supported: `claude-code`, `cc`):

```bash
r9s run cc --model "$R9S_MODEL"
```

Configure local tools:

```bash
r9s set claude-code
r9s reset claude-code
```

See all options:

```bash
r9s -h
r9s chat -h
r9s bot -h
r9s run -h
```

## Python SDK usage

Minimal example:

```python
from r9s import R9S

with R9S() as r9s:

    res = r9s.chat.create(model="gpt-4o-mini", messages=[
        {
            "role": "user",
            "content": "Hello, how are you?",
        },
    ], stream=False)
```

Advanced SDK usage: [docs/sdk-advanced.md](docs/sdk-advanced.md)
