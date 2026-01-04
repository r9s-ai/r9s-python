from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from difflib import unified_diff
from pathlib import Path
from typing import Dict, Optional

from r9s.agents.exceptions import AgentExistsError, AgentNotFoundError
from r9s.agents.local_store import (
    LocalAgentStore,
    LocalAuditStore,
    delete_agent,
    list_agents,
    load_agent,
    load_version,
    save_agent,
    save_version,
)
from r9s.agents.models import AgentStatus
from r9s.cli_tools.bots import load_bot
from r9s.cli_tools.ui.terminal import (
    FG_RED,
    FG_YELLOW,
    error,
    header,
    info,
    prompt_text,
    success,
    warning,
)


def _require_name(name: Optional[str]) -> str:
    if name and name.strip():
        return name.strip()
    raise SystemExit("agent name is required")


def _is_interactive() -> bool:
    return sys.stdin.isatty()


def _prompt_multiline_required(message: str) -> str:
    header(message)
    first = prompt_text("> ", color=FG_YELLOW)
    while not first:
        first = prompt_text("> ", color=FG_RED)
    lines = [first]
    while True:
        line = prompt_text("> ", color=FG_YELLOW)
        if not line:
            break
        lines.append(line)
    out = "\n".join(lines).rstrip()
    if not out:
        raise SystemExit("instructions cannot be empty")
    return out


def _require_model(model: Optional[str]) -> str:
    if model and model.strip():
        return model.strip()
    if _is_interactive():
        model = prompt_text("Model: ")
        if model:
            return model
    raise SystemExit("model is required")


def _parse_params(param_text: Optional[str]) -> Dict[str, object]:
    if not param_text:
        return {}
    try:
        data = json.loads(param_text)
    except json.JSONDecodeError as exc:
        raise SystemExit(f"Invalid params JSON: {exc}") from exc
    if not isinstance(data, dict):
        raise SystemExit("params must be a JSON object")
    return data


def _read_instructions_file(file_path: str) -> str:
    """Read instructions from a file."""
    path = Path(file_path).expanduser()
    if not path.exists():
        raise SystemExit(f"File not found: {file_path}")
    try:
        content = path.read_text(encoding="utf-8").strip()
    except OSError as exc:
        raise SystemExit(f"Failed to read file: {exc}") from exc
    if not content:
        raise SystemExit("Instructions file is empty")
    return content


def _edit_in_editor(initial_text: str = "", agent_name: str = "") -> str:
    """Open $EDITOR for editing instructions (like git commit)."""
    editor = os.environ.get("VISUAL") or os.environ.get("EDITOR", "vi")

    # Prepare initial content with help comments
    help_text = """
# Enter instructions for the agent above.
# Lines starting with '#' will be ignored.
# Save and close the editor to continue.
# Leave empty to abort.
"""
    if agent_name:
        help_text = f"# Agent: {agent_name}\n" + help_text

    content = initial_text + "\n" + help_text if initial_text else help_text.lstrip()

    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".md", delete=False, encoding="utf-8"
    ) as f:
        f.write(content)
        tmp_path = f.name

    try:
        result = subprocess.run([editor, tmp_path], check=False)
        if result.returncode != 0:
            raise SystemExit(f"Editor exited with code {result.returncode}")

        with open(tmp_path, encoding="utf-8") as f:
            lines = f.readlines()

        # Filter out comment lines
        filtered = [line for line in lines if not line.lstrip().startswith("#")]
        output = "".join(filtered).strip()

        if not output:
            raise SystemExit("Instructions cannot be empty (aborted)")

        return output
    finally:
        try:
            os.unlink(tmp_path)
        except OSError:
            pass


def _get_instructions(args: argparse.Namespace, existing: str = "") -> str:
    """Get instructions from various sources with priority:
    1. --instructions-file (highest)
    2. --edit (opens editor)
    3. --instructions (inline text)
    4. Interactive prompt (if TTY)
    """
    # Priority 1: File
    if getattr(args, "instructions_file", None):
        return _read_instructions_file(args.instructions_file)

    # Priority 2: Editor
    if getattr(args, "edit", False):
        return _edit_in_editor(existing, getattr(args, "name", ""))

    # Priority 3: Inline
    if args.instructions is not None:
        text = args.instructions.strip()
        if text:
            return text

    # Priority 4: Interactive
    if _is_interactive():
        info("Enter instructions for this agent.")
        return _prompt_multiline_required("Instructions (end with empty line):")

    raise SystemExit(
        "Missing instructions. Use --instructions, --instructions-file, or --edit"
    )


def handle_agent_list(_: argparse.Namespace) -> None:
    names = list_agents()
    if not names:
        info("No agents found.")
        return
    header("Agents")
    for name in names:
        try:
            agent = load_agent(name)
        except AgentNotFoundError:
            continue
        print(f"- {agent.name} (current: {agent.current_version})")


def handle_agent_show(args: argparse.Namespace) -> None:
    name = _require_name(args.name)
    agent = load_agent(name)
    header(f"Agent: {agent.name}")
    print(f"- id: {agent.id}")
    if agent.description:
        print(f"- description: {agent.description}")
    print(f"- current_version: {agent.current_version}")
    print(f"- created_at: {agent.created_at.isoformat()}")
    print(f"- updated_at: {agent.updated_at.isoformat()}")
    version = load_version(name, agent.current_version)
    print(f"- model: {version.model}")
    print(f"- provider: {version.provider}")
    print(f"- status: {version.status.value}")
    if version.variables:
        print(f"- variables: {', '.join(version.variables)}")


def handle_agent_create(args: argparse.Namespace) -> None:
    name = _require_name(args.name)
    instructions = _get_instructions(args)
    model = _require_model(args.model)
    provider = (args.provider or "r9s").strip()
    description = (args.description or "").strip()
    params = _parse_params(args.params)

    store = LocalAgentStore()
    try:
        agent = store.create(
            name,
            instructions=instructions,
            model=model,
            provider=provider,
            description=description,
            change_reason=args.reason or "",
            model_params=params,
        )
    except AgentExistsError as exc:
        raise SystemExit(str(exc)) from exc
    success(f"Created agent: {agent.name} (version {agent.current_version})")


def handle_agent_update(args: argparse.Namespace) -> None:
    name = _require_name(args.name)

    # Load existing instructions for editor pre-population
    existing_instructions = ""
    if getattr(args, "edit", False):
        try:
            agent = load_agent(name)
            version = load_version(name, agent.current_version)
            existing_instructions = version.instructions
        except AgentNotFoundError:
            pass

    instructions = _get_instructions(args, existing=existing_instructions)
    params = _parse_params(args.params)

    store = LocalAgentStore()
    try:
        update_kwargs = {
            "instructions": instructions,
            "model": args.model,
            "provider": args.provider,
            "change_reason": args.reason or "",
            "bump": args.bump,
        }
        if params:
            update_kwargs["model_params"] = params
        version = store.update(
            name,
            **update_kwargs,
        )
    except AgentNotFoundError as exc:
        raise SystemExit(str(exc)) from exc
    success(f"Updated agent: {name} -> {version.version}")


def handle_agent_delete(args: argparse.Namespace) -> None:
    name = _require_name(args.name)
    confirm = prompt_text(f"Delete agent '{name}'? [y/N]: ", color=FG_RED).lower()
    if confirm not in ("y", "yes"):
        warning("Cancelled.")
        return
    try:
        path = delete_agent(name)
    except AgentNotFoundError:
        error("Agent not found.")
        return
    success(f"Deleted: {path}")


def handle_agent_history(args: argparse.Namespace) -> None:
    name = _require_name(args.name)
    store = LocalAgentStore()
    versions = store.list_versions(name)
    if not versions:
        info("No versions found.")
        return
    header(f"Agent history: {name}")
    for version in versions:
        print(
            f"- {version.version} ({version.status.value})"
            + (f" parent={version.parent_version}" if version.parent_version else "")
        )


def handle_agent_diff(args: argparse.Namespace) -> None:
    name = _require_name(args.name)
    v1 = load_version(name, args.v1)
    v2 = load_version(name, args.v2)
    header(f"Diff: {name} {v1.version} -> {v2.version}")
    diff = unified_diff(
        v1.instructions.splitlines(),
        v2.instructions.splitlines(),
        fromfile=v1.version,
        tofile=v2.version,
        lineterm="",
    )
    print("\n".join(diff))


def handle_agent_rollback(args: argparse.Namespace) -> None:
    name = _require_name(args.name)
    version = args.version
    agent = load_agent(name)
    load_version(name, version)
    agent.current_version = version
    agent.updated_at = datetime.now(timezone.utc).replace(microsecond=0)
    save_agent(agent)
    success(f"Rolled back {name} to {version}")


def _update_status(name: str, version: str, status: AgentStatus) -> None:
    agent_version = load_version(name, version)
    agent_version.status = status
    save_version(name, agent_version)


def handle_agent_approve(args: argparse.Namespace) -> None:
    name = _require_name(args.name)
    _update_status(name, args.version, AgentStatus.APPROVED)
    success(f"Approved {name} {args.version}")


def handle_agent_deprecate(args: argparse.Namespace) -> None:
    name = _require_name(args.name)
    _update_status(name, args.version, AgentStatus.DEPRECATED)
    success(f"Deprecated {name} {args.version}")


def handle_agent_audit(args: argparse.Namespace) -> None:
    store = LocalAuditStore()
    entries = store.query(
        agent=_require_name(args.name),
        request_id=args.request_id,
        last=args.last,
    )
    if not entries:
        info("No audit entries found.")
        return
    header(f"Audit: {args.name}")
    for entry in entries:
        print(
            f"- {entry.timestamp.isoformat()} {entry.request_id}"
            f" {entry.agent_version} input={entry.input_tokens} output={entry.output_tokens}"
        )


def handle_agent_export(args: argparse.Namespace) -> None:
    name = _require_name(args.name)
    agent = load_agent(name)
    versions = LocalAgentStore().list_versions(name)
    payload = {
        "agent": {
            "id": agent.id,
            "name": agent.name,
            "description": agent.description,
            "current_version": agent.current_version,
            "created_at": agent.created_at.isoformat(),
            "updated_at": agent.updated_at.isoformat(),
        },
        "versions": [
            {
                "version": v.version,
                "content_hash": v.content_hash,
                "instructions": v.instructions,
                "model": v.model,
                "provider": v.provider,
                "tools": v.tools,
                "files": v.files,
                "variables": v.variables,
                "model_params": v.model_params,
                "created_at": v.created_at.isoformat(),
                "created_by": v.created_by,
                "change_reason": v.change_reason,
                "status": v.status.value,
                "parent_version": v.parent_version,
            }
            for v in versions
        ],
    }
    print(json.dumps(payload, ensure_ascii=False, indent=2))


def handle_agent_import_bot(args: argparse.Namespace) -> None:
    name = _require_name(args.name)
    model = _require_model(args.model)
    bot = load_bot(name)
    if not bot.system_prompt:
        raise SystemExit("Bot has no system_prompt to import.")
    store = LocalAgentStore()
    store.create(
        name,
        instructions=bot.system_prompt,
        model=model,
        provider=args.provider or "r9s",
        description=bot.description or "",
        change_reason="Imported from bot",
        model_params={
            "temperature": bot.temperature,
            "top_p": bot.top_p,
            "max_tokens": bot.max_tokens,
            "presence_penalty": bot.presence_penalty,
            "frequency_penalty": bot.frequency_penalty,
        },
    )
    success(f"Imported bot '{name}' as agent.")
