from __future__ import annotations

import argparse
import os
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Optional

import yaml

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
from r9s.skills.exceptions import InvalidSkillError, SecurityError, SkillNotFoundError
from r9s.skills.local_store import (
    delete_skill,
    list_skills,
    load_skill,
    save_skill,
    skill_path,
)
from r9s.skills.models import ScriptPolicy
from r9s.skills.validator import validate_skill_directory, validate_skill_name


def _require_name(name: Optional[str]) -> str:
    if name and name.strip():
        return name.strip()
    raise SystemExit("skill name is required")


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
    output = "\n".join(lines).rstrip()
    if not output:
        raise SystemExit("instructions cannot be empty")
    return output


def _read_text_file(path: str) -> str:
    target = Path(path).expanduser()
    if not target.exists():
        raise SystemExit(f"File not found: {path}")
    try:
        content = target.read_text(encoding="utf-8")
    except OSError as exc:
        raise SystemExit(f"Failed to read file: {exc}") from exc
    if not content.strip():
        raise SystemExit("File is empty")
    return content


def _build_skill_md(
    name: str,
    description: str,
    instructions: str,
    license_text: Optional[str] = None,
    compatibility: Optional[str] = None,
) -> str:
    payload = {"name": name, "description": description}
    if license_text:
        payload["license"] = license_text
    if compatibility:
        payload["compatibility"] = compatibility
    frontmatter = yaml.safe_dump(payload, sort_keys=False).strip()
    body = instructions.rstrip()
    return f"---\n{frontmatter}\n---\n\n{body}\n"


def _edit_in_editor(initial_text: str, skill_name: str) -> str:
    editor = os.environ.get("VISUAL") or os.environ.get("EDITOR", "vi")
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".md", delete=False, encoding="utf-8"
    ) as handle:
        handle.write(initial_text)
        tmp_path = handle.name
    try:
        result = subprocess.run([editor, tmp_path], check=False)
        if result.returncode != 0:
            raise SystemExit(f"Editor exited with code {result.returncode}")
        content = Path(tmp_path).read_text(encoding="utf-8").strip()
        if not content:
            raise SystemExit(f"SKILL.md cannot be empty for {skill_name}")
        return content
    finally:
        try:
            os.unlink(tmp_path)
        except OSError:
            pass


def handle_skill_list(_: argparse.Namespace) -> None:
    names = list_skills()
    if not names:
        info("No skills found.")
        return
    header("Skills")
    for name in names:
        print(f"- {name}")


def handle_skill_show(args: argparse.Namespace) -> None:
    name = _require_name(args.name)
    try:
        skill = load_skill(name)
    except (InvalidSkillError, SkillNotFoundError) as exc:
        raise SystemExit(str(exc)) from exc
    header(f"Skill: {skill.name}")
    print(f"- description: {skill.description}")
    if skill.license:
        print(f"- license: {skill.license}")
    if skill.compatibility:
        print(f"- compatibility: {skill.compatibility}")
    if skill.allowed_tools:
        print(f"- allowed_tools: {', '.join(skill.allowed_tools)}")
    if skill.scripts:
        print(f"- scripts: {', '.join(skill.scripts)}")
    if skill.references:
        print(f"- references: {', '.join(skill.references)}")
    if skill.assets:
        print(f"- assets: {', '.join(skill.assets)}")


def handle_skill_create(args: argparse.Namespace) -> None:
    try:
        name = validate_skill_name(_require_name(args.name))
    except InvalidSkillError as exc:
        raise SystemExit(str(exc)) from exc
    content: Optional[str] = None

    if args.file:
        content = _read_text_file(args.file)
    elif args.edit:
        description = (args.description or "").strip() or "TODO: description"
        instructions = (args.instructions or "").strip() or "# Instructions"
        template = _build_skill_md(name, description, instructions)
        content = _edit_in_editor(template, name)
    else:
        description = (args.description or "").strip()
        instructions = (args.instructions or "").strip()
        if not description and _is_interactive():
            description = prompt_text("Description: ").strip()
        if not instructions and _is_interactive():
            info("Enter skill instructions (end with empty line):")
            instructions = _prompt_multiline_required("Instructions:")
        if not description or not instructions:
            raise SystemExit(
                "description and instructions are required (use --file or --edit)"
            )
        content = _build_skill_md(
            name,
            description,
            instructions,
            license_text=(args.license or None),
            compatibility=(args.compatibility or None),
        )

    try:
        path = save_skill(name, content)
    except InvalidSkillError as exc:
        raise SystemExit(str(exc)) from exc
    success(f"Saved: {path}")


def handle_skill_validate(args: argparse.Namespace) -> None:
    name = _require_name(args.name)
    try:
        root = skill_path(name)
        policy = ScriptPolicy(allow_scripts=bool(args.allow_scripts))
        metadata = validate_skill_directory(root, policy=policy)
    except (InvalidSkillError, SkillNotFoundError, SecurityError) as exc:
        raise SystemExit(str(exc)) from exc
    header(f"Skill: {metadata.name}")
    success("Skill is valid.")


def handle_skill_delete(args: argparse.Namespace) -> None:
    name = _require_name(args.name)
    confirm = prompt_text(f"Delete skill '{name}'? [y/N]: ", color=FG_RED).lower()
    if confirm not in ("y", "yes"):
        warning("Cancelled.")
        return
    try:
        path = delete_skill(name)
    except (InvalidSkillError, SkillNotFoundError) as exc:
        error(str(exc))
        return
    success(f"Deleted: {path}")
