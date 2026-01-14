from __future__ import annotations

import hashlib
import json
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional


class AgentStatus(str, Enum):
    DRAFT = "draft"
    APPROVED = "approved"
    DEPRECATED = "deprecated"


def _utc_now() -> datetime:
    return datetime.now(timezone.utc).replace(microsecond=0)


def _hash_payload(payload: Dict[str, Any]) -> str:
    raw = json.dumps(payload, sort_keys=True, ensure_ascii=False)
    digest = hashlib.sha256(raw.encode("utf-8")).hexdigest()[:16]
    return f"sha256:{digest}"


@dataclass
class Agent:
    id: str
    name: str
    description: str = ""
    current_version: str = "1.0.0"
    created_at: datetime = field(default_factory=_utc_now)
    updated_at: datetime = field(default_factory=_utc_now)


@dataclass
class AgentVersion:
    version: str
    instructions: str
    model: str
    provider: str = "r9s"
    tools: List[Dict[str, Any]] = field(default_factory=list)
    files: List[Dict[str, Any]] = field(default_factory=list)
    skills: List[str] = field(default_factory=list)
    variables: List[str] = field(default_factory=list)
    model_params: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=_utc_now)
    created_by: str = ""
    change_reason: str = ""
    status: AgentStatus = AgentStatus.DRAFT
    parent_version: Optional[str] = None
    content_hash: str = field(init=False)

    def __post_init__(self) -> None:
        from r9s.agents.template import extract_variables

        extracted = extract_variables(self.instructions)
        if extracted:
            self.variables = extracted
        payload = {
            "instructions": self.instructions,
            "model": self.model,
            "provider": self.provider,
            "tools": self.tools,
            "files": self.files,
            "skills": self.skills,
            "variables": self.variables,
            "model_params": self.model_params,
        }
        self.content_hash = _hash_payload(payload)


@dataclass
class AgentExecution:
    agent_name: str
    agent_version: str
    content_hash: str
    execution_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    request_id: str = ""
    model: str = ""
    provider: str = ""
    timestamp: datetime = field(default_factory=_utc_now)
    input_tokens: int = 0
    output_tokens: int = 0
    session_id: Optional[str] = None
