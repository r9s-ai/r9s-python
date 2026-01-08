"""Load skills and format for injection into system prompt."""
from __future__ import annotations

from pathlib import Path
from typing import List, Optional

from r9s.skills.exceptions import SkillNotFoundError
from r9s.skills.local_store import load_skill, skill_path
from r9s.skills.models import Skill


def load_skills(skill_refs: List[str], warn_fn=None) -> List[Skill]:
    """Load skills by reference.

    Currently only local skills are supported.
    Remote refs (github:, r9s:, https:) are skipped with a warning.

    Args:
        skill_refs: List of skill references (local names only for now)
        warn_fn: Optional function to call with warning messages

    Returns:
        List of loaded Skill objects
    """
    skills = []
    for ref in skill_refs:
        # Phase 3: local only (no github:, r9s:, https:)
        if ":" in ref:
            if warn_fn:
                warn_fn(f"Skipping remote skill ref (not yet supported): {ref}")
            continue
        try:
            skill = load_skill(ref)
            skills.append(skill)
        except SkillNotFoundError:
            if warn_fn:
                warn_fn(f"Skill not found: {ref}")
            continue
    return skills


def resolve_skill_script(script_name: str, skills: List[Skill]) -> Optional[Path]:
    """Resolve a skill script path if it exists in loaded skills."""
    for skill in skills:
        if script_name in skill.scripts:
            return skill_path(skill.name) / script_name
    return None


def format_skills_context(skills: List[Skill]) -> str:
    """Format skills as markdown for system prompt injection.

    Args:
        skills: List of Skill objects to format

    Returns:
        Formatted markdown string to append to system prompt
    """
    if not skills:
        return ""

    lines = ["\n## Skills\n"]
    lines.append("The following skills are available to guide your responses:\n")

    for skill in skills:
        lines.append(f"### {skill.name}\n")
        if skill.description:
            lines.append(f"*{skill.description}*\n")
        lines.append(skill.instructions.strip())
        lines.append("\n")

    return "\n".join(lines)


def build_system_prompt_with_skills(
    agent_instructions: str,
    skill_refs: List[str],
    warn_fn=None,
) -> str:
    """Combine agent instructions with loaded skills.

    Args:
        agent_instructions: Base agent system prompt
        skill_refs: List of skill references to load
        warn_fn: Optional function for warnings

    Returns:
        Combined system prompt with skills appended
    """
    if not skill_refs:
        return agent_instructions

    skills = load_skills(skill_refs, warn_fn=warn_fn)
    skills_context = format_skills_context(skills)

    if skills_context:
        return f"{agent_instructions}\n{skills_context}"
    return agent_instructions
