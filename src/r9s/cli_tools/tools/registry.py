from __future__ import annotations

from typing import Dict, List, Optional, Set

from r9s.cli_tools.ui.terminal import ToolName

from .base import ToolIntegration
from .claude_code import ClaudeCodeIntegration
from .codex import CodexIntegration
from .qwen_code import QwenCodeIntegration


class ToolRegistry:
    def __init__(self) -> None:
        self._registry: Dict[ToolName, ToolIntegration] = {}

    def register(self, name: ToolName, tool: ToolIntegration) -> None:
        self._registry[name] = tool

    def get(self, name: ToolName) -> Optional[ToolIntegration]:
        return self._registry.get(name)

    def primary_names(self) -> List[ToolName]:
        names = sorted({str(tool.primary_name) for tool in self._registry.values()})
        return [ToolName(name) for name in names]

    def resolve(self, name: ToolName) -> Optional[ToolIntegration]:
        if name in self._registry:
            return self._registry[name]
        normalized = name.lower().replace("_", "-")
        return self._registry.get(ToolName(normalized))


APPS = ToolRegistry()

_claude_code = ClaudeCodeIntegration()
for alias in _claude_code.aliases:
    APPS.register(ToolName(alias), _claude_code)

_codex = CodexIntegration()
for alias in _codex.aliases:
    APPS.register(ToolName(alias), _codex)

_qwen_code = QwenCodeIntegration()
for alias in _qwen_code.aliases:
    APPS.register(ToolName(alias), _qwen_code)


def supported_app_names_for_config() -> List[str]:
    primary = [str(x) for x in APPS.primary_names()]
    supported: Set[str] = set(primary)
    # Public alias
    if "claude-code" in supported:
        supported.add("cc")
    return sorted(supported)


def supported_app_names_for_run() -> List[str]:
    supported: Set[str] = set()
    for name in APPS.primary_names():
        tool = APPS.resolve(name)
        if tool and tool.supports_run():
            supported.add(str(name))
    if "claude-code" in supported:
        supported.add("cc")
    return sorted(supported)

