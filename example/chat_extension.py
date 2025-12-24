"""
一个最小的 r9s chat 扩展示例。

用法：
  r9s chat --model <MODEL> --ext example/chat_extension.py

或者：
  export R9S_CHAT_EXTENSIONS=example/chat_extension.py
  r9s chat --model <MODEL>
"""

from __future__ import annotations

from r9s.cli_tools.chat_extensions import ChatContext, ChatExtensionRegistry


class DemoExtension:
    name = "demo"

    def on_user_input(self, text: str, ctx: ChatContext) -> str:
        return text.strip()

    def on_stream_delta(self, delta: str, ctx: ChatContext) -> str:
        return delta

    def after_response(self, text: str, ctx: ChatContext) -> str:
        return text


def register(registry: ChatExtensionRegistry) -> None:
    registry.add(DemoExtension())
