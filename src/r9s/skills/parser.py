from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Tuple

import yaml

from r9s.skills.exceptions import InvalidSkillError
from r9s.skills.models import SkillMetadata


def _split_frontmatter(content: str) -> Tuple[str, str]:
    lines = content.splitlines()
    if not lines or lines[0].strip() != "---":
        raise InvalidSkillError("Missing YAML frontmatter")
    end_index = None
    for idx in range(1, len(lines)):
        if lines[idx].strip() == "---":
            end_index = idx
            break
    if end_index is None:
        raise InvalidSkillError("Unterminated YAML frontmatter")
    yaml_text = "\n".join(lines[1:end_index]).strip()
    body = "\n".join(lines[end_index + 1 :]).lstrip("\n")
    return yaml_text, body


def _parse_allowed_tools(raw: Any) -> List[str]:
    if raw is None:
        return []
    if isinstance(raw, str):
        return [item for item in raw.split() if item]
    if isinstance(raw, list):
        tools: List[str] = []
        for item in raw:
            if not isinstance(item, str):
                raise InvalidSkillError("allowed-tools must contain strings")
            cleaned = item.strip()
            if cleaned:
                tools.append(cleaned)
        return tools
    raise InvalidSkillError("allowed-tools must be a string or list")


def _parse_metadata(data: Dict[str, Any]) -> SkillMetadata:
    name = str(data.get("name", "")).strip()
    description = str(data.get("description", "")).strip()
    if not name:
        raise InvalidSkillError("Skill name is required")
    if not description:
        raise InvalidSkillError("Skill description is required")

    license_text = data.get("license")
    compatibility = data.get("compatibility")
    metadata = data.get("metadata") or {}
    if not isinstance(metadata, dict):
        raise InvalidSkillError("metadata must be a mapping")

    allowed_raw = data.get("allowed-tools")
    if allowed_raw is None:
        allowed_raw = data.get("allowed_tools")
    allowed_tools = _parse_allowed_tools(allowed_raw)

    return SkillMetadata(
        name=name,
        description=description,
        license=str(license_text) if license_text is not None else None,
        compatibility=str(compatibility) if compatibility is not None else None,
        metadata=metadata,
        allowed_tools=allowed_tools,
    )


def parse_skill_markdown(content: str) -> Tuple[SkillMetadata, str]:
    if not content.strip():
        raise InvalidSkillError("SKILL.md is empty")
    yaml_text, body = _split_frontmatter(content)
    try:
        data = yaml.safe_load(yaml_text) if yaml_text else {}
    except yaml.YAMLError as exc:
        raise InvalidSkillError(f"Invalid YAML frontmatter: {exc}") from exc
    if data is None:
        data = {}
    if not isinstance(data, dict):
        raise InvalidSkillError("YAML frontmatter must be a mapping")
    metadata = _parse_metadata(data)
    return metadata, body


def parse_skill_file(path: Path) -> Tuple[SkillMetadata, str]:
    try:
        content = path.read_text(encoding="utf-8")
    except OSError as exc:
        raise InvalidSkillError(f"Failed to read {path}: {exc}") from exc
    return parse_skill_markdown(content)
