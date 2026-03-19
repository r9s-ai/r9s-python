# r9s Web UI (Streamlit)

`r9s web` provides a lightweight Streamlit-based web UI for managing local agents, chatting, and generating images in your browser.

## When to use

- Prefer a browser UI over terminal workflows for day-to-day chat/image generation
- Want a visual way to create/update/roll back local agents (stored under `~/.r9s/agents/`)
- Need quick iteration across models and agents

## Install

The Web UI is shipped as an optional dependency:

```bash
pip install "r9s[web]"
```

## Launch

```bash
r9s web --open-browser
```

Common options:

```bash
# Bind to all interfaces (e.g. containers / remote hosts)
r9s web --host 0.0.0.0 --port 8501

# By default, if the port is in use, r9s will auto-pick a free one.
# To fail fast instead:
r9s web --host 0.0.0.0 --port 8501 --no-auto-port

# Override via flags (you can also fill in the sidebar)
r9s web --api-key ... --base-url https://api.r9s.ai/v1 --model gpt-5-mini
```

## Configuration

Provide these either in the sidebar after launch or via environment variables:

- `R9S_API_KEY`: required
- `R9S_BASE_URL`: default `https://api.r9s.ai/v1`
- `R9S_MODEL`: optional default for the Chat page (you can also pick from the model dropdown)
- `R9S_IMAGE_MODEL`: optional for the Images page (passed to `images.create(model=...)`)

## Pages

### Chat

- Supports plain text chat
- Supports uploading an image for the current turn (embedded as `data:<mime>;base64,...`)
- Supports streaming output (enabled by default)
- Optionally use a local agent as the system prompt (supports `{{var}}` template variables; variables are entered as JSON)

### Agents

Visual management for local agents (default directory: `~/.r9s/agents/`, override via `R9S_AGENTS_DIR`):

- Create an agent (name / model / provider / instructions / skills)
- Edit and save (creates a new version, matching the CLI `r9s agent update` semantics)
- Delete an agent
- Roll back versions (sets `current_version`)

### Image generation

- Provide a prompt and choose `n/size/response_format`
- Optionally set `model` (otherwise server defaults apply)
- Renders `url` or `b64_json` responses

## Notes

- The Web UI handles `R9S_API_KEY` in the browser. Avoid using it on untrusted machines or shared browser profiles.
- This is a minimal UI: it reuses the SDK’s `chat`/`images` and local agent storage, and does not include advanced CLI features like history persistence or chat extensions.
