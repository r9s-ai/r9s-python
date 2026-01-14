from __future__ import annotations

import os
from pathlib import Path
from typing import List, Optional

from r9s.skills.exceptions import InvalidSkillError, SkillNotFoundError
from r9s.skills.models import ScriptPolicy, Skill
from r9s.skills.parser import parse_skill_file, parse_skill_markdown
from r9s.skills.validator import (
    ensure_within_root,
    validate_metadata,
    validate_skill_directory,
    validate_skill_name,
)


def skills_root() -> Path:
    env = os.getenv("R9S_SKILLS_DIR")
    if env:
        return Path(env).expanduser()
    return Path.home() / ".r9s" / "skills"


def skill_path(name: str) -> Path:
    safe = validate_skill_name(name)
    return skills_root() / safe


def skill_manifest_path(name: str) -> Path:
    return skill_path(name) / "SKILL.md"


def list_skills() -> List[str]:
    root = skills_root()
    if not root.exists():
        return []
    skills = []
    for path in root.iterdir():
        if not path.is_dir():
            continue
        if (path / "SKILL.md").exists():
            skills.append(path.name)
    return sorted(skills)


def save_skill(name: str, content: str) -> Path:
    safe = validate_skill_name(name)
    metadata, _ = parse_skill_markdown(content)
    validate_metadata(metadata, expected_name=safe)
    root = skill_path(safe)
    root.mkdir(parents=True, exist_ok=True)
    manifest = skill_manifest_path(safe)
    manifest.write_text(content, encoding="utf-8")
    return manifest


def load_skill(name: str, *, policy: Optional[ScriptPolicy] = None) -> Skill:
    safe = validate_skill_name(name)
    path = skill_manifest_path(safe)
    if not path.exists():
        raise SkillNotFoundError(f"Skill not found: {safe}")
    metadata, instructions = parse_skill_file(path)
    validate_metadata(metadata, expected_name=safe)
    skill_dir = skill_path(safe)
    if policy is not None:
        validate_skill_directory(skill_dir, policy=policy)
    return Skill(
        name=metadata.name,
        description=metadata.description,
        instructions=instructions,
        source="local",
        source_ref=None,
        license=metadata.license,
        compatibility=metadata.compatibility,
        metadata=metadata.metadata,
        allowed_tools=metadata.allowed_tools,
        scripts=_list_assets(skill_dir, "scripts"),
        references=_list_assets(skill_dir, "references"),
        assets=_list_assets(skill_dir, "assets"),
    )


def delete_skill(name: str) -> Path:
    safe = validate_skill_name(name)
    path = skill_path(safe)
    if not path.exists():
        raise SkillNotFoundError(f"Skill not found: {safe}")
    for child in sorted(path.rglob("*"), reverse=True):
        if child.is_file() or child.is_symlink():
            child.unlink()
        elif child.is_dir():
            child.rmdir()
    path.rmdir()
    return path


def _list_assets(root: Path, subdir: str) -> List[str]:
    target = root / subdir
    if not target.exists():
        return []
    ensure_within_root(root, target)
    assets: List[str] = []
    for item in sorted(target.rglob("*")):
        if item.is_file() or item.is_symlink():
            ensure_within_root(root, item)
            assets.append(item.relative_to(root).as_posix())
    return assets
