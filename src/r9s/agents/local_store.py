from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

try:
    import tomllib  # pyright: ignore[reportMissingImports]
except Exception:  # pragma: no cover
    tomllib = None  # type: ignore[assignment]

try:
    import tomli  # pyright: ignore[reportMissingImports]
except Exception:  # pragma: no cover
    tomli = None  # type: ignore[assignment]

from r9s.agents.exceptions import (
    AgentExistsError,
    AgentNotFoundError,
    VersionNotFoundError,
)
from r9s.agents.models import Agent, AgentExecution, AgentStatus, AgentVersion
from r9s.agents.store import AgentStore, AuditStore
from r9s.agents.template import extract_variables
from r9s.agents.versioning import increment_version


def _utc_now() -> datetime:
    return datetime.now(timezone.utc).replace(microsecond=0)


def _load_toml(path: Path) -> Dict[str, Any]:
    raw = path.read_bytes()
    if tomllib is not None:
        data = tomllib.loads(raw.decode("utf-8"))
    elif tomli is not None:
        data = tomli.loads(raw.decode("utf-8"))
    else:
        raise RuntimeError("TOML parser is not available (need tomllib or tomli)")
    if not isinstance(data, dict):
        raise ValueError(f"invalid toml file: {path}")
    return data


def _toml_quote(value: str) -> str:
    return json.dumps(value, ensure_ascii=False)


def _toml_multiline(value: str) -> str:
    # TOML spec: newline after opening delimiter is trimmed, but trailing newlines are kept.
    # So we only add leading \n (which gets trimmed), not trailing \n.
    if "'''" not in value:
        return "'''\n" + value + "'''"
    if '"""' not in value:
        return '"""\n' + value + '"""'
    return _toml_quote(value)


def _toml_format_value(value: Any) -> str:
    if isinstance(value, str):
        return _toml_quote(value)
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, (int, float)):
        return str(value)
    if value is None:
        return """"""  # empty string for lack of null
    if isinstance(value, list):
        items = ", ".join(
            _toml_format_value(item) for item in value if item is not None
        )
        return f"[{items}]"
    if isinstance(value, dict):
        parts = []
        for key, val in value.items():
            if val is None:
                continue
            parts.append(f"{key} = {_toml_format_value(val)}")
        return "{ " + ", ".join(parts) + " }"
    return _toml_quote(str(value))


def _format_datetime(value: datetime) -> str:
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc).replace(microsecond=0).isoformat()


def _parse_datetime(value: Any) -> datetime:
    if isinstance(value, datetime):
        return value
    if isinstance(value, str):
        try:
            dt = datetime.fromisoformat(value)
        except ValueError:
            return _utc_now()
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt
    return _utc_now()


def agents_root() -> Path:
    env = os.getenv("R9S_AGENTS_DIR")
    if env:
        return Path(env).expanduser()
    return Path.home() / ".r9s" / "agents"


def _validate_agent_name(name: str) -> str:
    safe = name.strip()
    if not safe:
        raise ValueError("agent name cannot be empty")
    if safe in {".", ".."}:
        raise ValueError("agent name cannot be '.' or '..'")
    if "\x00" in safe:
        raise ValueError("agent name cannot contain null bytes")
    if Path(safe).name != safe:
        raise ValueError("agent name cannot contain path separators")
    return safe


def agent_path(name: str) -> Path:
    safe = _validate_agent_name(name)
    return agents_root() / safe


def read_agent_name_from_manifest(path: Path) -> str:
    data = _load_toml(path)
    name = str(data.get("name", "")).strip()
    if not name:
        raise ValueError("agent manifest missing name")
    return _validate_agent_name(name)


def agent_manifest_path(name: str) -> Path:
    return agent_path(name) / "agent.toml"


def versions_root(name: str) -> Path:
    return agent_path(name) / "versions"


def version_path(name: str, version: str) -> Path:
    return versions_root(name) / f"{version}.toml"


def audit_path(name: str) -> Path:
    return agent_path(name) / "audit.jsonl"


def _dump_agent_toml(agent: Agent) -> str:
    lines = [
        f"id = {_toml_quote(agent.id)}",
        f"name = {_toml_quote(agent.name)}",
        f"description = {_toml_quote(agent.description)}",
        f"current_version = {_toml_quote(agent.current_version)}",
        f"created_at = {_toml_quote(_format_datetime(agent.created_at))}",
        f"updated_at = {_toml_quote(_format_datetime(agent.updated_at))}",
    ]
    return "\n".join(lines).rstrip() + "\n"


def save_agent(agent: Agent) -> Path:
    root = agent_path(agent.name)
    root.mkdir(parents=True, exist_ok=True)
    manifest = agent_manifest_path(agent.name)
    manifest.write_text(_dump_agent_toml(agent), encoding="utf-8")
    versions_root(agent.name).mkdir(parents=True, exist_ok=True)
    return manifest


def load_agent(name: str) -> Agent:
    path = agent_manifest_path(name)
    if not path.exists():
        raise AgentNotFoundError(f"Agent not found: {name}")
    data = _load_toml(path)
    return Agent(
        id=str(data.get("id", "")),
        name=str(data.get("name", name)).strip(),
        description=str(data.get("description", "")),
        current_version=str(data.get("current_version", "1.0.0")),
        created_at=_parse_datetime(data.get("created_at")),
        updated_at=_parse_datetime(data.get("updated_at")),
    )


def list_agents() -> List[str]:
    root = agents_root()
    if not root.exists():
        return []
    return sorted([p.name for p in root.iterdir() if p.is_dir()])


def delete_agent(name: str) -> Path:
    path = agent_path(name)
    if not path.exists():
        raise AgentNotFoundError(f"Agent not found: {name}")
    for child in sorted(path.rglob("*"), reverse=True):
        if child.is_file() or child.is_symlink():
            child.unlink()
        elif child.is_dir():
            child.rmdir()
    path.rmdir()
    return path


def _dump_version_toml(version: AgentVersion) -> str:
    lines = [
        f"version = {_toml_quote(version.version)}",
        f"content_hash = {_toml_quote(version.content_hash)}",
    ]
    if version.parent_version:
        lines.append(f"parent_version = {_toml_quote(version.parent_version)}")
    lines.extend(
        [
            f"created_at = {_toml_quote(_format_datetime(version.created_at))}",
            f"created_by = {_toml_quote(version.created_by)}",
            f"change_reason = {_toml_quote(version.change_reason)}",
            f"status = {_toml_quote(version.status.value)}",
            f"model = {_toml_quote(version.model)}",
            f"provider = {_toml_quote(version.provider)}",
        ]
    )
    if version.skills:
        lines.append(f"skills = {_toml_format_value(version.skills)}")
    if version.model_params:
        lines.append("\n[params]")
        for key, val in version.model_params.items():
            if val is None:
                continue
            lines.append(f"{key} = {_toml_format_value(val)}")
    lines.append("\n[instructions]")
    lines.append(f"value = {_toml_multiline(version.instructions)}")
    if version.variables:
        lines.append(f"variables = {_toml_format_value(version.variables)}")
    if version.tools:
        for tool in version.tools:
            lines.append("\n[[tools]]")
            for key, val in tool.items():
                if val is None:
                    continue
                lines.append(f"{key} = {_toml_format_value(val)}")
    if version.files:
        for entry in version.files:
            lines.append("\n[[files]]")
            for key, val in entry.items():
                if val is None:
                    continue
                lines.append(f"{key} = {_toml_format_value(val)}")
    return "\n".join(lines).rstrip() + "\n"


def save_version(name: str, version: AgentVersion) -> Path:
    root = versions_root(name)
    root.mkdir(parents=True, exist_ok=True)
    path = version_path(name, version.version)
    path.write_text(_dump_version_toml(version), encoding="utf-8")
    return path


def _coerce_status(value: Any) -> AgentStatus:
    if isinstance(value, AgentStatus):
        return value
    if isinstance(value, str):
        try:
            return AgentStatus(value)
        except ValueError:
            return AgentStatus.DRAFT
    return AgentStatus.DRAFT


def load_version(name: str, version: str) -> AgentVersion:
    if version == "latest":
        version = resolve_latest_version(name)
    path = version_path(name, version)
    if not path.exists():
        raise VersionNotFoundError(f"Version not found: {name}@{version}")
    data = _load_toml(path)

    instructions = ""
    variables_from_instructions: List[str] = []
    instructions_data = data.get("instructions")
    if isinstance(instructions_data, dict) and "value" in instructions_data:
        instructions = str(instructions_data.get("value", ""))
        variables = instructions_data.get("variables")
        if isinstance(variables, list):
            variables_from_instructions = [str(v) for v in variables]
    elif isinstance(instructions_data, str):
        instructions = instructions_data
    if not instructions:
        instructions = str(data.get("instructions", ""))

    variables_raw = data.get("variables")
    variables: List[str] = []
    if variables_from_instructions:
        variables = variables_from_instructions
    elif isinstance(variables_raw, list):
        variables = [str(v) for v in variables_raw]
    elif isinstance(variables_raw, dict):
        variables = [str(k) for k in variables_raw.keys()]
    else:
        variables = extract_variables(instructions)

    skills_raw = data.get("skills", [])
    skills: List[str] = (
        [str(s) for s in skills_raw] if isinstance(skills_raw, list) else []
    )

    version_obj = AgentVersion(
        version=str(data.get("version", version)),
        instructions=instructions,
        model=str(data.get("model", "")),
        provider=str(data.get("provider", "r9s")),
        tools=data.get("tools", []) if isinstance(data.get("tools"), list) else [],
        files=data.get("files", []) if isinstance(data.get("files"), list) else [],
        skills=skills,
        variables=variables,
        model_params=data.get("params", {})
        if isinstance(data.get("params"), dict)
        else {},
        created_at=_parse_datetime(data.get("created_at")),
        created_by=str(data.get("created_by", "")),
        change_reason=str(data.get("change_reason", "")),
        status=_coerce_status(data.get("status")),
        parent_version=str(data.get("parent_version"))
        if data.get("parent_version")
        else None,
    )

    stored_hash = data.get("content_hash")
    if isinstance(stored_hash, str) and stored_hash and stored_hash != version_obj.content_hash:
        raise ValueError("content_hash mismatch")
    return version_obj


def list_versions(name: str) -> List[str]:
    root = versions_root(name)
    if not root.exists():
        return []
    return sorted([p.stem for p in root.glob("*.toml")])


def resolve_latest_version(name: str) -> str:
    versions = list_versions(name)
    if not versions:
        raise VersionNotFoundError(f"No versions found for agent: {name}")
    versions_sorted = sorted(versions, key=lambda v: [int(x) for x in v.split(".")])
    return versions_sorted[-1]


def load_versions(name: str) -> List[AgentVersion]:
    out = []
    for ver in list_versions(name):
        try:
            out.append(load_version(name, ver))
        except Exception:
            continue
    out.sort(key=lambda v: [int(x) for x in v.version.split(".")])
    return out


def _default_created_by() -> str:
    return os.getenv("R9S_AGENT_USER", "")


class LocalAgentStore(AgentStore):
    def get_agent(self, name: str) -> Agent:
        return load_agent(name)

    def get_version(self, name: str, version: str = "latest") -> AgentVersion:
        return load_version(name, version)

    def create(self, name: str, **config: object) -> Agent:
        if agent_path(name).exists():
            raise AgentExistsError(f"Agent already exists: {name}")
        instructions = str(config.get("instructions", ""))
        model = str(config.get("model", ""))
        provider = str(config.get("provider", "r9s"))
        description = str(config.get("description", ""))
        created_by = str(config.get("created_by", "")) or _default_created_by()
        change_reason = str(config.get("change_reason", ""))
        model_params = config.get("model_params", {})
        tools = config.get("tools", [])
        files = config.get("files", [])
        skills = config.get("skills", [])
        now = _utc_now()

        agent = Agent(
            id=config.get("id", "") or f"agt_{uuid()}",
            name=name.strip(),
            description=description,
            current_version="1.0.0",
            created_at=now,
            updated_at=now,
        )
        version = AgentVersion(
            version="1.0.0",
            instructions=instructions,
            model=model,
            provider=provider,
            tools=list(tools) if isinstance(tools, list) else [],
            files=list(files) if isinstance(files, list) else [],
            skills=list(skills) if isinstance(skills, list) else [],
            model_params=model_params if isinstance(model_params, dict) else {},
            created_at=now,
            created_by=created_by,
            change_reason=change_reason,
            status=AgentStatus.DRAFT,
        )
        save_agent(agent)
        save_version(agent.name, version)
        return agent

    def update(self, name: str, **config: object) -> AgentVersion:
        agent = load_agent(name)
        current_version = load_version(name, agent.current_version)
        bump = str(config.get("bump", "patch"))
        new_version = increment_version(current_version.version, bump=bump)
        instructions = str(config.get("instructions", current_version.instructions))
        model = str(config.get("model", current_version.model))
        provider = str(config.get("provider", current_version.provider))
        created_by = str(config.get("created_by", "")) or _default_created_by()
        change_reason = str(config.get("change_reason", ""))
        if "model_params" in config and isinstance(config.get("model_params"), dict):
            model_params = config.get("model_params", {})
        else:
            model_params = current_version.model_params
        tools = (
            config.get("tools", current_version.tools)
            if isinstance(config.get("tools", current_version.tools), list)
            else current_version.tools
        )
        files = (
            config.get("files", current_version.files)
            if isinstance(config.get("files", current_version.files), list)
            else current_version.files
        )
        skills = (
            config.get("skills", current_version.skills)
            if isinstance(config.get("skills", current_version.skills), list)
            else current_version.skills
        )

        version = AgentVersion(
            version=new_version,
            instructions=instructions,
            model=model,
            provider=provider,
            tools=list(tools) if isinstance(tools, list) else [],
            files=list(files) if isinstance(files, list) else [],
            skills=list(skills) if isinstance(skills, list) else [],
            model_params=model_params if isinstance(model_params, dict) else {},
            created_at=_utc_now(),
            created_by=created_by,
            change_reason=change_reason,
            status=AgentStatus.DRAFT,
            parent_version=current_version.version,
        )
        save_version(agent.name, version)
        agent.current_version = new_version
        agent.updated_at = _utc_now()
        save_agent(agent)
        return version

    def list(self) -> List[Agent]:
        out = []
        for name in list_agents():
            try:
                out.append(load_agent(name))
            except AgentNotFoundError:
                continue
        return out

    def list_versions(self, name: str) -> List[AgentVersion]:
        return load_versions(name)

    def delete(self, name: str) -> None:
        delete_agent(name)


class LocalAuditStore(AuditStore):
    def record(self, execution: AgentExecution) -> None:
        path = audit_path(execution.agent_name)
        path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "execution_id": execution.execution_id,
            "agent_name": execution.agent_name,
            "agent_version": execution.agent_version,
            "content_hash": execution.content_hash,
            "request_id": execution.request_id,
            "model": execution.model,
            "provider": execution.provider,
            "timestamp": _format_datetime(execution.timestamp),
            "input_tokens": execution.input_tokens,
            "output_tokens": execution.output_tokens,
            "session_id": execution.session_id,
        }
        with path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(payload, ensure_ascii=False) + "\n")

    def _load_all(self, name: str) -> List[AgentExecution]:
        path = audit_path(name)
        if not path.exists():
            return []
        entries: List[AgentExecution] = []
        for line in path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            try:
                data = json.loads(line)
            except json.JSONDecodeError:
                continue
            if not isinstance(data, dict):
                continue
            entries.append(
                AgentExecution(
                    agent_name=str(data.get("agent_name", name)),
                    agent_version=str(data.get("agent_version", "")),
                    content_hash=str(data.get("content_hash", "")),
                    execution_id=str(data.get("execution_id", "")),
                    request_id=str(data.get("request_id", "")),
                    model=str(data.get("model", "")),
                    provider=str(data.get("provider", "")),
                    timestamp=_parse_datetime(data.get("timestamp")),
                    input_tokens=int(data.get("input_tokens", 0) or 0),
                    output_tokens=int(data.get("output_tokens", 0) or 0),
                    session_id=data.get("session_id"),
                )
            )
        return entries

    def query(self, **filters: object) -> List[AgentExecution]:
        name = str(filters.get("agent", ""))
        if not name:
            return []
        entries = self._load_all(name)
        request_id = str(filters.get("request_id", ""))
        if request_id:
            entries = [e for e in entries if e.request_id == request_id]
        start_time = filters.get("start_time")
        if isinstance(start_time, datetime):
            entries = [e for e in entries if e.timestamp >= start_time]
        end_time = filters.get("end_time")
        if isinstance(end_time, datetime):
            entries = [e for e in entries if e.timestamp <= end_time]
        last = filters.get("last")
        if isinstance(last, int) and last > 0:
            entries = entries[-last:]
        limit = filters.get("limit")
        if isinstance(limit, int) and limit > 0:
            entries = entries[:limit]
        return entries

    def export(self, format: str = "json") -> bytes:
        fmt = format.lower()
        if fmt != "json":
            raise ValueError("only json export is supported")
        payload = []
        root = agents_root()
        if root.exists():
            for name in sorted([p.name for p in root.iterdir() if p.is_dir()]):
                for entry in self._load_all(name):
                    payload.append(
                        {
                            "execution_id": entry.execution_id,
                            "agent_name": entry.agent_name,
                            "agent_version": entry.agent_version,
                            "content_hash": entry.content_hash,
                            "request_id": entry.request_id,
                            "model": entry.model,
                            "provider": entry.provider,
                            "timestamp": _format_datetime(entry.timestamp),
                            "input_tokens": entry.input_tokens,
                            "output_tokens": entry.output_tokens,
                            "session_id": entry.session_id,
                        }
                    )
        return json.dumps(payload, ensure_ascii=False, indent=2).encode("utf-8")


def uuid() -> str:
    return os.urandom(8).hex()
