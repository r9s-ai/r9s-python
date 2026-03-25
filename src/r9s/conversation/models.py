from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Literal, Optional

from r9s.models.message import MessageTypedDict


ConversationProtocol = Literal["chat_completions"]
ConversationEventType = Literal["probe", "text_delta", "done"]


@dataclass
class ConversationRequest:
    api_key: str
    base_url: str
    model: str
    messages: List[MessageTypedDict]
    temperature: Optional[float] = None
    top_p: Optional[float] = None
    max_tokens: Optional[int] = None
    presence_penalty: Optional[float] = None
    frequency_penalty: Optional[float] = None
    protocol: Optional[ConversationProtocol] = None
    http_headers: Optional[Dict[str, str]] = None


@dataclass
class ConversationEvent:
    type: ConversationEventType
    text: str = ""
    request_id: str = ""
    input_tokens: int = 0
    output_tokens: int = 0
    protocol: ConversationProtocol = "chat_completions"
    raw: Any = None


@dataclass
class ConversationResult:
    text: str
    request_id: str = ""
    input_tokens: int = 0
    output_tokens: int = 0
    protocol: ConversationProtocol = "chat_completions"
    raw: Any = None
