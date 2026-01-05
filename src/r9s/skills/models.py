from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class SkillMetadata:
    name: str
    description: str
    license: Optional[str] = None
    compatibility: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    allowed_tools: List[str] = field(default_factory=list)


@dataclass
class Skill:
    name: str
    description: str
    instructions: str
    source: str
    source_ref: Optional[str] = None
    license: Optional[str] = None
    compatibility: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    allowed_tools: List[str] = field(default_factory=list)
    scripts: List[str] = field(default_factory=list)
    references: List[str] = field(default_factory=list)
    assets: List[str] = field(default_factory=list)


@dataclass
class ScriptPolicy:
    """Policy controlling script execution for skills.

    TODO: Phase 2+ will add sandbox controls:
        allow_network: bool = False
        allow_filesystem: bool = False
        allow_env_vars: bool = False
        timeout_seconds: int = 30
        allowed_commands: List[str] = field(default_factory=list)
    """

    allow_scripts: bool = False
