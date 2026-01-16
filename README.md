<div align="center">

# r9s

**The official Python SDK and CLI for the r9s API**

![PyPI - Version](https://img.shields.io/pypi/v/r9s)
![PyPI - Downloads](https://img.shields.io/pypi/dm/r9s)
![Python Version](https://img.shields.io/pypi/pyversions/r9s)
<!-- [![GitHub Release](https://img.shields.io/github/v/release/r9s-ai/r9s-python)](https://github.com/r9s-ai/r9s-python/releases) -->
[![Ask DeepWiki](https://deepwiki.com/badge.svg)](https://deepwiki.com/r9s-ai/r9s-python)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](https://opensource.org/licenses/MIT)
[![GitHub Stars](https://img.shields.io/github/stars/r9s-ai/r9s-python?style=social)](https://github.com/r9s-ai/r9s-python)

</div>
---

:rocket: [Quick Start](#quick-start) - :computer: [CLI Usage](#cli-usage) - :books: [SDK Usage](#python-sdk-usage) - :wrench: [Development](#development)


## Quick start

**Requires Python 3.11+**

Install:

```bash
pip install r9s
```

Or directly execute the CLI:

```bash
uvx r9s
```

Set your API key via `.env` file (recommended) or environment variable:

```bash
# Option 1: Create .env in your project directory
cat > .env << 'EOF'
R9S_API_KEY=your_api_key
R9S_BASE_URL=https://api.r9s.ai/v1
R9S_MODEL=gpt-5-mini
EOF

# Option 2: Export environment variables
export R9S_API_KEY="your_api_key"
```

The CLI automatically loads `.env` from the current directory (SDK usage does not auto-load). Disable with `R9S_NO_DOTENV=1`.

## CLI usage

Chat (interactive, streaming by default):

```bash
r9s chat
```

Chat (stdin, useful for scripts/pipes):

```bash
echo "hello" | r9s chat
cat image.png | r9s chat
```

Resume a saved chat session (interactive selection):

```bash
r9s chat --resume
```

Agents (versioned, with audit trails, stored under `~/.r9s/agents/<name>/`):

```bash
# Create an agent
r9s agent create reviewer \
  --instructions "You are a code reviewer. Focus on bugs and security." \
  --model gpt-5-mini

# Chat with the agent
r9s chat --agent reviewer

# Agents support variables
r9s agent create code-reviewer \
  --instructions "Review {{language}} code for {{focus_areas}}" \
  --model gpt-5-mini

r9s chat --agent code-reviewer --var language=Python --var focus_areas="security, performance"

# Pull an agent definition from git
r9s agent pull github:my-org/agent-definitions --path agents/reviewer
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

Configure local tools (supported: `claude-code`, `cc`, `codex`, `qwen-code`):

```bash
r9s set claude-code
r9s reset claude-code
```

Enable bash completion:

```bash
eval "$(r9s completion bash)"
```

Web UI (Streamlit):

```bash
pip install "r9s[web]"
r9s web --open-browser
```

More details: [docs/web-ui.md](docs/web-ui.md)

List available models:

```bash
r9s models
r9s models --details  # Show owner and creation date
```

Audio (TTS, transcription, translation):

```bash
# Text to speech
r9s audio speech "Hello world" -o hello.mp3
r9s audio speech "Welcome" -o welcome.wav -v nova

# Speech to text (transcription)
r9s audio transcribe recording.mp3
r9s audio transcribe meeting.wav -o transcript.txt -f text

# Translate audio to English
r9s audio translate chinese_audio.mp3 -o english.txt
```

See all options:

```bash
r9s -h
r9s chat -h
r9s agent -h
r9s command -h
r9s audio -h
r9s models -h
r9s run -h
```

## Python SDK usage

Minimal example (reads `R9S_API_KEY` and optional `R9S_BASE_URL` from the environment):

```python
from r9s.client import R9S

with R9S.from_env() as r9s:

    res = r9s.chat.create(model="gpt-4o-mini", messages=[
        {
            "role": "user",
            "content": "Hello, how are you?",
        },
    ], stream=False)
```

Advanced SDK usage: [docs/sdk-advanced.md](docs/sdk-advanced.md)

## Development

Clone and install in editable mode with dev dependencies:

```bash
git clone https://github.com/r9s-ai/r9s-python.git
cd r9s-python
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -e ".[dev,test]"
```

Run tests:

```bash
pytest
```

Run linting/type checks:

```bash
ruff check src/
pyright
mypy src/
```
