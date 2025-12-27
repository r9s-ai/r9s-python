# Adding a New Tool Adapter

This guide explains how to add support for a new editor/IDE or tool (called an “app” in the CLI) to the `r9s` CLI.

Once added, it can be configured via:

```bash
r9s set <app>
r9s reset <app>
```

Some apps may also support:

```bash
r9s run <app> --model "$R9S_MODEL"
```

The examples below assume basic familiarity with Python and the existing Claude Code integration.

## Overview

Tool adapters live under `src/r9s/cli_tools/tools/` and follow a common interface provided by `ToolIntegration` in `src/r9s/cli_tools/tools/base.py`.

At a high level, a tool adapter:

- Knows where its configuration file lives (e.g. `~/.mytool/config.json`).
- Knows where to store backups (e.g. `~/.r9s/backup/my-tool/`).
- Implements `set_config` to:
  - Create a backup of the current config (if any).
  - Update the config to use the r9s API.
- Inherits common backup/restore helpers from `ToolIntegration`.
- (Optional) Implements `run_executable` + `run_env` to support `r9s run <app>`.

Once registered in the adapter registry, users can configure the tool with a single command.

## 1. Create a new adapter class

Create a new module under `src/r9s/cli_tools/tools/`, for example:

```text
src/r9s/cli_tools/tools/my_tool.py
```

Inside, define a class that inherits from `ToolIntegration` and sets up basic metadata:

```python
from pathlib import Path

from r9s.cli_tools.tools.base import ToolConfigSetResult, ToolIntegration


class MyToolIntegration(ToolIntegration):
    primary_name = "my-tool"
    aliases = ["my-tool", "my_tool"]

    def __init__(self) -> None:
        # Where the tool stores its config
        self._settings_path = Path.home() / ".mytool" / "config.json"

        # Where r9s should store backups for this tool
        self._backup_dir = Path.home() / ".r9s" / "backup" / "my-tool"

    def set_config(
        self,
        *,
        base_url: str,
        api_key: str,
        model: str,
        small_model: str,
        wire_api: str = "responses",
        reasoning_effort: str | None = None,
    ) -> ToolConfigSetResult:
        # Implemented in the next section
        ...
```

Notes:

- `primary_name` is the canonical CLI name (what you expect users to type).
- `aliases` lists any additional names you want to resolve to the same tool.
- `_settings_path` and `_backup_dir` are required for the base class to manage backups and restores.
- `small_model`, `wire_api`, and `reasoning_effort` are part of the shared adapter interface. If your tool doesn’t use them, accept and ignore them.

## 2. Implement `set_config`

The `set_config` method is responsible for:

- Optionally backing up the existing config.
- Reading the current config (if any).
- Updating it with r9s‑specific values.
- Writing the new config to disk.

`ToolIntegration` provides a `_create_backup_if_exists()` helper that handles the backup logic for you.

Example implementation for a JSON‑based config:

```python
import json

from r9s.cli_tools.tools.base import ToolConfigSetResult


class MyToolIntegration(ToolIntegration):
    # primary_name, aliases, __init__ as shown above

    def set_config(
        self,
        *,
        base_url: str,
        api_key: str,
        model: str,
        small_model: str,
        wire_api: str = "responses",
        reasoning_effort: str | None = None,
    ) -> ToolConfigSetResult:
        # 1) Create backup if a config file already exists
        backup_path = self._create_backup_if_exists()

        # 2) Read existing settings (if any)
        data: dict
        if self._settings_path.exists():
            try:
                with self._settings_path.open("r", encoding="utf-8") as fp:
                    existing = json.load(fp)
            except (json.JSONDecodeError, OSError):
                existing = {}
            data = existing if isinstance(existing, dict) else {}
        else:
            data = {}

        # 3) Apply r9s‑specific configuration
        #    Adapt this structure to your tool's config format.
        env = data.get("env")
        if not isinstance(env, dict):
            env = {}

        env.update(
            {
                "MYTOOL_BASE_URL": base_url,
                "MYTOOL_API_KEY": api_key,
                "MYTOOL_MODEL": model,
            }
        )

        data["env"] = env

        # 4) Write updated settings
        self._settings_path.parent.mkdir(parents=True, exist_ok=True)
        with self._settings_path.open("w", encoding="utf-8") as fp:
            json.dump(data, fp, indent=2, ensure_ascii=False)
            fp.write("\n")

        return ToolConfigSetResult(target_path=self._settings_path, backup_path=backup_path)
```

Key points:

- Always preserve unrelated existing fields where possible.
- Use the existing config structure of the tool (the example uses an `env` map similar to Claude Code).
- The backup file will be created under `_backup_dir` with a name like:

  ```text
  config.json.YYYYMMDDHHMMSS.bak
  ```

## 3. Register the adapter in the adapter registry

To make the new tool available to users, register it in `src/r9s/cli_tools/tools/registry.py`.

1. Import your integration:

   ```python
   from .my_tool import MyToolIntegration
   ```

2. Instantiate and register it with the registry:

   ```python
   APPS = ToolRegistry()

   _claude_code = ClaudeCodeIntegration()
   for alias in _claude_code.aliases:
       APPS.register(ToolName(alias), _claude_code)

   _my_tool = MyToolIntegration()
   for alias in _my_tool.aliases:
       APPS.register(ToolName(alias), _my_tool)
   ```

After this, the following will work:

```bash
r9s set my-tool
r9s reset my-tool
```

Users can also omit the tool name and choose it from the interactive menu.

## 4. (Optional) Support `r9s run <app>`

If your app can be launched from the terminal and can read credentials/endpoint/model from environment variables, you can support:

```bash
r9s run <app> --model "$R9S_MODEL"
```

To do that, implement these methods:

- `run_executable() -> str | None`: the executable name, e.g. `"claude"`.
- `run_env(api_key, base_url, model) -> dict[str, str]`: env vars injected before launching the app.

Example:

```python
class MyToolIntegration(ToolIntegration):
    def run_executable(self) -> str:
        return "mytool"

    def run_env(self, *, api_key: str, base_url: str, model: str) -> dict[str, str]:
        return {
            "MYTOOL_API_KEY": api_key,
            "MYTOOL_BASE_URL": base_url,
            "MYTOOL_MODEL": model,
        }
```

Apps will be listed under `r9s run -h` automatically if `supports_run()` is true (default: `run_executable() is not None`).

## 4. Manual testing checklist

Before shipping a new adapter, manually test the basic flows:

1. **Setup flow**

   ```bash
   export R9S_API_KEY="test-api-key"
   export R9S_BASE_URL="https://api.r9s.ai/v1"

   r9s set my-tool
   ```

   - Confirm the CLI:
     - Fetches/asks for a model.
     - Shows a correct configuration summary.
   - Verify on disk:
     - `~/.r9s/backup/my-tool/` contains a timestamped backup (if a config existed).
     - The tool's config file (e.g. `~/.mytool/config.json`) now includes the r9s settings.

2. **Restore flow**

   ```bash
   r9s reset my-tool
   ```

   - Confirm the CLI lists backups and restores from the chosen one.
   - Verify the config file content matches the expected backup.

   3. **Edge cases**

   - No existing config file: `set_config` should create a new config without errors.
   - Corrupted/invalid config file: `set_config` should handle JSON parse errors gracefully and still write a valid config.
   - No backups: `r9s reset my-tool` should print a clear message and exit without crashing.

## 5. Design guidelines

When building new adapters, keep these principles in mind:

- **Be conservative with user configs**
  - Only modify the fields needed for r9s.
  - Preserve other fields and formatting where reasonable.

- **Always back up before writing**
  - Use `_create_backup_if_exists()` so users can safely roll back.

- **Use stable paths**
  - Keep backup directories under:

    ```text
    ~/.r9s/backup/<tool-name>/
    ```

  - This matches the Claude Code integration and keeps things predictable.

- **Prefer simple, robust formats**
  - JSON is a good default if the tool supports it.
  - If the tool uses another format (INI, TOML, YAML), make sure you handle parsing and error cases carefully.

Following this guide, adding a new tool adapter should only require:

1. One new class under `src/r9s/cli_tools/tools/`.
2. A couple of lines in `src/r9s/cli_tools/tools/registry.py` to register it.
