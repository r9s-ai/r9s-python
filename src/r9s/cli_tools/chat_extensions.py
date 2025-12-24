from __future__ import annotations

import importlib
import importlib.machinery
import importlib.util
import os
from dataclasses import dataclass, field
from pathlib import Path
from types import ModuleType
from typing import Any, Iterable, List, Optional, Protocol, Sequence, cast, runtime_checkable

from r9s import models


@dataclass
class ChatContext:
    base_url: str
    model: str
    system_prompt: Optional[str] = None
    history_file: Optional[str] = None
    history: List[models.MessageTypedDict] = field(default_factory=list)


@runtime_checkable
class ChatExtension(Protocol):
    name: str


class ChatExtensionRegistry:
    def __init__(self) -> None:
        self._exts: List[ChatExtension] = []

    def add(self, ext: ChatExtension) -> None:
        if not isinstance(ext, ChatExtension):
            raise TypeError("Extension must define a 'name' attribute")
        self._exts.append(ext)

    def list(self) -> List[ChatExtension]:
        return list(self._exts)


def _load_module_from_file(path: Path) -> ModuleType:
    module_name = f"r9s_chat_ext_{path.stem}_{abs(hash(str(path)))}"
    loader = importlib.machinery.SourceFileLoader(module_name, str(path))
    spec = importlib.util.spec_from_loader(module_name, loader)
    if spec is None or spec.loader is None:
        raise ImportError(f"Failed to load extension file: {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)  # type: ignore[attr-defined]
    return module


def _load_module(spec: str) -> ModuleType:
    path = Path(spec)
    if path.exists() and path.is_file() and path.suffix == ".py":
        return _load_module_from_file(path)
    return importlib.import_module(spec)


def _register_from_module(module: ModuleType, registry: ChatExtensionRegistry) -> None:
    register = getattr(module, "register", None)
    if callable(register):
        register(registry)
        return

    get_extension = getattr(module, "get_extension", None)
    if callable(get_extension):
        registry.add(cast(ChatExtension, get_extension()))
        return

    for attr in ("EXTENSION", "extension"):
        ext = getattr(module, attr, None)
        if ext is not None:
            registry.add(cast(ChatExtension, ext))
            return

    raise ImportError(
        "Extension must provide one of: register(registry) / get_extension() / EXTENSION / extension"
    )


def parse_extension_specs(cli_specs: Sequence[str]) -> List[str]:
    env = os.getenv("R9S_CHAT_EXTENSIONS", "")
    env_specs = [s.strip() for s in env.split(",") if s.strip()]
    return [*env_specs, *[s for s in cli_specs if s]]


def load_extensions(specs: Sequence[str]) -> List[ChatExtension]:
    registry = ChatExtensionRegistry()
    for spec in specs:
        module = _load_module(spec)
        _register_from_module(module, registry)
    return registry.list()


def _maybe_call(ext: Any, method: str, *args: Any, **kwargs: Any) -> Any:
    fn = getattr(ext, method, None)
    if callable(fn):
        return fn(*args, **kwargs)
    return None


def run_user_input_extensions(exts: Iterable[ChatExtension], text: str, ctx: ChatContext) -> str:
    out = text
    for ext in exts:
        result = _maybe_call(ext, "on_user_input", out, ctx)
        if isinstance(result, str):
            out = result
    return out


def run_before_request_extensions(
    exts: Iterable[ChatExtension],
    messages: List[models.MessageTypedDict],
    ctx: ChatContext,
) -> List[models.MessageTypedDict]:
    out = messages
    for ext in exts:
        result = _maybe_call(ext, "before_request", out, ctx)
        if isinstance(result, list):
            out = cast(List[models.MessageTypedDict], result)
    return out


def run_stream_delta_extensions(exts: Iterable[ChatExtension], delta: str, ctx: ChatContext) -> str:
    out = delta
    for ext in exts:
        result = _maybe_call(ext, "on_stream_delta", out, ctx)
        if isinstance(result, str):
            out = result
    return out


def run_after_response_extensions(
    exts: Iterable[ChatExtension], assistant_text: str, ctx: ChatContext
) -> str:
    out = assistant_text
    for ext in exts:
        result = _maybe_call(ext, "after_response", out, ctx)
        if isinstance(result, str):
            out = result
    return out


def run_command_extensions(exts: Iterable[ChatExtension], command: str, ctx: ChatContext) -> bool:
    handled = False
    for ext in exts:
        result = _maybe_call(ext, "on_command", command, ctx)
        if result is True:
            handled = True
    return handled
