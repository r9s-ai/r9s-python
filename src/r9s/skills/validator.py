from __future__ import annotations

import re
from pathlib import Path
from typing import Optional

from r9s.skills.exceptions import InvalidSkillError, SecurityError, SkillNotFoundError
from r9s.skills.models import ScriptPolicy, SkillMetadata
from r9s.skills.parser import parse_skill_file

_NAME_RE = re.compile(r"^[a-z0-9][a-z0-9-]{0,63}$")


def validate_skill_name(name: str) -> str:
    cleaned = name.strip()
    if not cleaned:
        raise InvalidSkillError("Skill name cannot be empty")
    if "/" in cleaned or "\\" in cleaned:
        raise InvalidSkillError("Skill name cannot contain path separators")
    if not _NAME_RE.match(cleaned):
        raise InvalidSkillError(
            "Skill name must be 1-64 chars: lowercase letters, numbers, hyphens"
        )
    return cleaned


def ensure_within_root(root: Path, target: Path) -> None:
    root_resolved = root.resolve()
    target_resolved = target.resolve()
    if root_resolved != target_resolved and root_resolved not in target_resolved.parents:
        raise SecurityError(f"Path traversal detected: {target}")


def validate_metadata(metadata: SkillMetadata, expected_name: Optional[str] = None) -> None:
    validate_skill_name(metadata.name)
    if expected_name and metadata.name != expected_name:
        raise InvalidSkillError(
            f"Skill name mismatch: expected '{expected_name}', got '{metadata.name}'"
        )
    if not metadata.description:
        raise InvalidSkillError("Skill description cannot be empty")
    if len(metadata.description) > 1024:
        raise InvalidSkillError("Skill description exceeds 1024 characters")


def validate_skill_directory(
    skill_dir: Path, *, policy: Optional[ScriptPolicy] = None
) -> SkillMetadata:
    if not skill_dir.exists():
        raise SkillNotFoundError(f"Skill not found: {skill_dir.name}")
    manifest = skill_dir / "SKILL.md"
    if not manifest.exists():
        raise SkillNotFoundError(f"SKILL.md missing for skill: {skill_dir.name}")
    metadata, _ = parse_skill_file(manifest)
    validate_metadata(metadata, expected_name=skill_dir.name)
    policy = policy or ScriptPolicy()
    scripts_dir = skill_dir / "scripts"
    if scripts_dir.exists() and any(scripts_dir.rglob("*")):
        if not policy.allow_scripts:
            raise SecurityError(
                "Skill includes scripts but --allow-scripts was not provided"
            )
    return metadata
