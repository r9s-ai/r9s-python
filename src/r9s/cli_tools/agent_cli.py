from __future__ import annotations

import argparse
import json
import os
import shutil
import stat
import subprocess
import sys
import tarfile
import tempfile
import urllib.request
import zipfile
from datetime import datetime, timezone
from difflib import unified_diff
from pathlib import Path
from typing import Dict, Optional

from r9s.agents.exceptions import AgentExistsError, AgentNotFoundError
from r9s.agents.local_store import (
    LocalAgentStore,
    LocalAuditStore,
    agent_path,
    delete_agent,
    list_agents,
    load_agent,
    load_version,
    read_agent_name_from_manifest,
    save_agent,
    save_version,
)
from r9s.agents.models import AgentStatus
from r9s.cli_tools.bots import load_bot
from r9s.cli_tools.ui.rich_output import print_markdown
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


def _resolve_model(model: Optional[str]) -> str:
    """Resolve model from argument, environment, or interactive prompt."""
    if model and model.strip():
        return model.strip()
    # Fall back to R9S_MODEL environment variable
    env_model = os.environ.get("R9S_MODEL", "").strip()
    if env_model:
        return env_model
    # Interactive prompt as last resort
    if _is_interactive():
        model = prompt_text("Model (or set R9S_MODEL): ")
        if model:
            return model
    raise SystemExit("model is required (use --model or set R9S_MODEL)")


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

    1. --instructions-file (highest) - explicit file path
    2. --edit - opens $EDITOR
    3. --instructions @filename - file reference (like curl, gh)
       - @- reads from stdin
       - @@ escapes literal @ (e.g., "@@mention" -> "@mention")
    4. --instructions "text" - inline text
    5. Interactive prompt (if TTY)
    """
    # Priority 1: Explicit file flag
    if getattr(args, "instructions_file", None):
        return _read_instructions_file(args.instructions_file)

    # Priority 2: Editor
    if getattr(args, "edit", False):
        return _edit_in_editor(existing, getattr(args, "name", ""))

    # Priority 3 & 4: Inline or @filename convention
    instr = getattr(args, "instructions", None)
    if instr is not None:
        text = instr.strip()
        if text:
            if text.startswith("@"):
                # @@ escape sequence: "@@text" -> "@text"
                if text.startswith("@@"):
                    return text[1:]
                # @filename convention (like curl, gh)
                filename = text[1:].strip()
                if not filename:
                    raise SystemExit(
                        "Invalid --instructions: '@' must be followed by a filename (or @- for stdin)"
                    )
                # @- reads from stdin
                if filename == "-":
                    content = sys.stdin.read().strip()
                    if not content:
                        raise SystemExit("No instructions provided on stdin")
                    return content
                return _read_instructions_file(filename)
            return text

    # Priority 5: Interactive
    if _is_interactive():
        info("Enter instructions for this agent.")
        return _prompt_multiline_required("Instructions (end with empty line):")

    raise SystemExit(
        "Missing instructions. Use --instructions, --instructions-file, or --edit"
    )


def _is_within(path: Path, root: Path) -> bool:
    try:
        path.resolve().relative_to(root.resolve())
    except ValueError:
        return False
    return True


def _is_git_ref(ref: str) -> bool:
    if ref.startswith("github:"):
        return True
    if ref.startswith("git@") or ref.startswith("ssh://"):
        return True
    return ref.endswith(".git")


def _normalize_git_ref(ref: str) -> str:
    if not ref.startswith("github:"):
        return ref
    slug = ref[len("github:") :].strip("/")
    if not slug or "/" not in slug:
        raise SystemExit("Invalid GitHub reference (expected github:owner/repo)")
    return f"https://github.com/{slug}.git"


def _clone_repo(ref: str, dest: Path) -> None:
    repo = _normalize_git_ref(ref)
    result = subprocess.run(
        ["git", "clone", "--depth", "1", repo, str(dest)],
        check=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    if result.returncode != 0:
        stderr = result.stderr.strip() or result.stdout.strip()
        raise SystemExit(f"git clone failed: {stderr or 'unknown error'}")


def _download_archive(url: str, dest: Path, max_bytes: int = 50 * 1024 * 1024) -> Path:
    request = urllib.request.Request(url, headers={"User-Agent": "r9s-agent-pull"})
    with urllib.request.urlopen(request) as response:
        size = response.headers.get("Content-Length")
        if size and int(size) > max_bytes:
            raise SystemExit("Archive too large to download")
        out_path = dest / Path(url).name
        total = 0
        with open(out_path, "wb") as handle:
            while True:
                chunk = response.read(1024 * 1024)
                if not chunk:
                    break
                total += len(chunk)
                if total > max_bytes:
                    raise SystemExit("Archive exceeds size limit")
                handle.write(chunk)
    return out_path


def _safe_extract_zip(archive: Path, dest: Path) -> None:
    with zipfile.ZipFile(archive) as zf:
        for member in zf.infolist():
            if stat.S_IFMT(member.external_attr >> 16) == stat.S_IFLNK:
                raise SystemExit("Archive contains symlinks")
            target = dest / member.filename
            if not _is_within(target, dest):
                raise SystemExit("Archive contains invalid paths")
            if member.is_dir():
                target.mkdir(parents=True, exist_ok=True)
            else:
                target.parent.mkdir(parents=True, exist_ok=True)
                with zf.open(member) as src, open(target, "wb") as dst:
                    shutil.copyfileobj(src, dst)


def _safe_extract_tar(archive: Path, dest: Path) -> None:
    with tarfile.open(archive) as tf:
        for member in tf.getmembers():
            target = dest / member.name
            if not _is_within(target, dest):
                raise SystemExit("Archive contains invalid paths")
            if member.issym() or member.islnk():
                raise SystemExit("Archive contains symlinks")
            if not (member.isdir() or member.isreg()):
                raise SystemExit("Archive contains unsupported entries")
        tf.extractall(dest)


def _resolve_bundle_path(root: Path, path: Optional[str]) -> Path:
    base = root
    if path:
        base = (root / path).resolve()
    if not base.exists():
        raise SystemExit("Bundle path not found")
    if not base.is_dir():
        raise SystemExit("Bundle path must be a directory")
    if not _is_within(base, root):
        raise SystemExit("Bundle path escapes repository")
    return base


def _copy_agent_bundle(src: Path, dest: Path, name_override: Optional[str]) -> str:
    manifest = src / "agent.toml"
    if not manifest.exists() or not manifest.is_file() or manifest.is_symlink():
        raise SystemExit("agent.toml not found in bundle")
    versions_dir = src / "versions"
    if (
        not versions_dir.exists()
        or not versions_dir.is_dir()
        or versions_dir.is_symlink()
    ):
        raise SystemExit("versions/ directory not found in bundle")

    agent_name = read_agent_name_from_manifest(manifest)
    final_name = name_override.strip() if name_override else agent_name
    if not final_name:
        raise SystemExit("agent name cannot be empty")

    dest.mkdir(parents=True, exist_ok=True)
    dest_manifest = dest / "agent.toml"
    shutil.copy2(manifest, dest_manifest)

    dest_versions = dest / "versions"
    dest_versions.mkdir(parents=True, exist_ok=True)
    for entry in versions_dir.iterdir():
        if entry.is_symlink():
            raise SystemExit("Bundle contains symlinks")
        if entry.is_file() and entry.suffix == ".toml":
            shutil.copy2(entry, dest_versions / entry.name)

    if final_name != agent_name:
        agent_data = load_agent(final_name)
        agent_data.name = final_name
        save_agent(agent_data)

    return final_name


def _cleanup_agent_dir(name: str) -> None:
    try:
        delete_agent(name)
    except Exception:
        pass


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
    if getattr(args, "instructions", False):
        print()
        header("Instructions")
        print_markdown(version.instructions)


def handle_agent_create(args: argparse.Namespace) -> None:
    name = _require_name(args.name)
    instructions = _get_instructions(args)
    model = _resolve_model(args.model)
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
    except AgentExistsError:
        raise SystemExit(
            f"Agent '{name}' already exists. Use 'r9s agent update {name}' to modify it."
        )
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
    model = _resolve_model(args.model)
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


def handle_agent_pull(args: argparse.Namespace) -> None:
    ref = args.ref.strip()
    name_override = (args.name or "").strip() or None
    path = args.path
    force = getattr(args, "force", False)

    with tempfile.TemporaryDirectory() as temp_dir:
        temp_root = Path(temp_dir)
        if _is_git_ref(ref):
            repo_dir = temp_root / "repo"
            _clone_repo(ref, repo_dir)
            bundle_root = _resolve_bundle_path(repo_dir, path)
        else:
            local_path = Path(ref).expanduser()
            if local_path.exists():
                bundle_root = _resolve_bundle_path(local_path, path)
            elif ref.startswith("http://") or ref.startswith("https://"):
                try:
                    archive = _download_archive(ref, temp_root)
                except Exception as exc:
                    raise SystemExit(f"Failed to download archive: {exc}") from exc
                extract_dir = temp_root / "extract"
                extract_dir.mkdir(parents=True, exist_ok=True)
                if archive.suffix == ".zip":
                    _safe_extract_zip(archive, extract_dir)
                elif archive.name.endswith((".tar.gz", ".tgz")):
                    _safe_extract_tar(archive, extract_dir)
                else:
                    raise SystemExit("Unsupported archive format (use .zip or .tar.gz)")
                bundle_root = _resolve_bundle_path(extract_dir, path)
            else:
                raise SystemExit("Unsupported source (use git ref, local path, or HTTP archive)")

        manifest = bundle_root / "agent.toml"
        agent_name = read_agent_name_from_manifest(manifest)
        final_name = name_override or agent_name
        dest = agent_path(final_name)

        if dest.exists():
            if not force:
                raise SystemExit(f"Agent already exists: {final_name} (use --force)")
            _cleanup_agent_dir(final_name)

        final_name = _copy_agent_bundle(bundle_root, dest, name_override)
        try:
            agent = load_agent(final_name)
            load_version(final_name, agent.current_version)
            for version_file in (dest / "versions").glob("*.toml"):
                load_version(final_name, version_file.stem)
        except Exception as exc:
            _cleanup_agent_dir(final_name)
            raise SystemExit(f"Invalid agent bundle: {exc}") from exc

    success(f"Pulled agent '{final_name}'")
