# r9s CLI – Developer & Advanced Usage Guide

This document describes how the `r9s` CLI works, how to use it beyond the basic flow, and how to extend it to new tools.

The main entry point lives in `r9s/cli.py`.

## Features overview

- `r9s set [tool]`
  - Interactive setup to wire a tool to the r9s API.
  - Reads/asks for `R9S_API_KEY` and `R9S_BASE_URL`.
  - Fetches model list from `$R9S_BASE_URL/v1/model` when possible.
  - Backs up existing config before writing a new one.
- `r9s reset [tool]`
  - Restores a previous config from backups created by `set`.

Currently only **Claude Code** is supported. Tool‑specific logic lives in `r9s/tools`.

## Environment variables

- `R9S_API_KEY`  
  API key used by the CLI. If not set, the CLI prompts and hides input.

- `R9S_BASE_URL`  
  Base URL for r9s. Resolution order:

  1. `--base-url` flag (if provided)
  2. `R9S_BASE_URL` environment variable
  3. Fallback: `https://api.r9s.ai`

  If neither the flag nor the environment variable is set, the CLI silently uses the default URL and does not prompt the user.

These variables can also be passed explicitly on the command line via flags (see below).

## Commands in detail

### `r9s set`

Basic usage:

```bash
r9s set [tool]
```

Supported tool names:

- `claude-code`
- `claude`
- `claude_code`

If `tool` is omitted, the CLI shows a menu and lets the user choose.

Interactive flow:

1. **Resolve API key**
   - Use `R9S_API_KEY` if set.
   - Otherwise prompt the user via `getpass()` (no echo).

2. **Select tool**
   - If a tool name was provided, it is resolved via the tool registry.
   - Otherwise a list of supported primary tool names is shown.

3. **Choose model**
   - Calls `GET $R9S_BASE_URL/v1/models` with header:

     ```http
     Authorization: Bearer <R9S_API_KEY>
     ```
   - If the response is:
     - A list of strings → treated as model IDs.
     - A JSON object with `data: [{id: "..."}]` → extracts the `id` values.
   - If the request fails or the format is not recognized, the user is asked to enter a model name manually.

4. **Confirm settings**
   - Shows tool name, base URL, model, and a masked API key.
   - Writes the configuration only after the user confirms with `y`.

5. **Write & backup**
   - Each tool implementation is responsible for:
     - Creating a timestamped backup of the existing config.
     - Writing the new config.

#### Flags

You can pre‑fill most values via flags, then still get a confirmation step:

```bash
r9s set claude-code \
  --api-key "$R9S_API_KEY" \
  --base-url "$R9S_BASE_URL" \
  --model "r9s-code-1"
```

Flags:

- `--api-key` – override or replace `R9S_API_KEY`.
- `--base-url` – override or replace `R9S_BASE_URL`.
- `--model` – skip model selection and use the given model.

### `r9s reset`

Usage:

```bash
r9s reset [tool]
```

Flow:

1. **Select tool** – same resolution logic as `set`.
2. **List backups** – the tool implementation returns an ordered list of backup files.
3. **Choose backup**
   - By default, the latest backup is used.
   - If multiple backups exist, the user can pick one by index.
4. **Confirm restore**
   - The CLI shows the chosen backup path.
   - On confirmation, the backup overwrites the current config.

## Claude Code integration

Implementation: `r9s/tools/claude_code.py`

### Paths

- Main settings file:

  ```text
  ~/.claude/settings.json
  ```

- Backup directory:

  ```text
  ~/.r9s/backup/claude-code/
  ```

  Backups are named:

  ```text
  settings.json.YYYYMMDDHHMMSS.bak
  ```

### What gets written

The Claude Code integration:

1. Reads `~/.claude/settings.json` (if it exists and is valid JSON).
2. Ensures there is a top‑level `env` object.
3. Updates/sets these keys:

```json
{
  "env": {
    "ANTHROPIC_BASE_URL": "$BASE_URL",
    "ANTHROPIC_AUTH_TOKEN": "$API_KEY",
    "API_TIMEOUT_MS": "3000000",
    "CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC": 1,
    "ANTHROPIC_MODEL": "$MODEL",
    "ANTHROPIC_SMALL_FAST_MODEL": "$MODEL"
  }
}
```

All other existing fields in `settings.json` are preserved.

### Backup behavior

- Before any write, if `~/.claude/settings.json` exists, it is copied to:

  ```text
  ~/.r9s/backup/claude-code/settings.json.YYYYMMDDHHMMSS.bak
  ```

- `r9s reset claude-code` chooses one of these backups and copies it back to `~/.claude/settings.json`.

## Extending to new tools

You can add support for new tools by following the same pattern as the Claude Code integration.

1. **Create a tool integration**

   - Add a module under `r9s/tools/`, e.g. `r9s/tools/my_tool.py`.
   - Implement a class with the same interface as `ToolIntegration` in `r9s/tools/base.py`:
     - `primary_name: str`
     - `aliases: List[str]`
     - `set_config(base_url: str, api_key: str, model: str) -> ToolConfigSetResult`
     - `list_backups() -> List[Path]`
     - `reset_config(backup_path: Path) -> Path`

2. **Register the tool**

   - In `r9s/cli.py`, instantiate your integration and register its aliases in the `ToolRegistry`.

3. **Keep behavior consistent**

   - Always create a backup before writing user config.
   - Try to keep paths and naming predictable, e.g.:

     ```text
     ~/.r9s/backup/<tool-name>/
     ```

   - Preserve any unrelated fields in existing config files.

With this pattern, adding support for new editors/IDEs or tools should be straightforward without changing the core CLI flow.
