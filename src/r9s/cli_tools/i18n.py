from __future__ import annotations

import os
from typing import Dict

SUPPORTED_LANGS = ("en", "zh-CN")

_ALIASES = {
    "en": "en",
    "en-us": "en",
    "en_us": "en",
    "zh": "zh-CN",
    "zh-cn": "zh-CN",
    "zh_cn": "zh-CN",
    "cn": "zh-CN",
}


def resolve_lang(value: str | None) -> str:
    raw = (value or os.getenv("R9S_LANG") or "").strip()
    if not raw:
        return "en"
    normalized = raw.lower().replace(" ", "").replace("_", "-")
    return _ALIASES.get(normalized, "en")


_STRINGS: Dict[str, Dict[str, str]] = {
    "en": {
        "cli.title": "r9s CLI",
        "cli.tagline": "Chat with r9s, manage bots, or configure local dev tools to use r9s.",
        "cli.examples.title": "Common usage examples:",
        "cli.examples.chat_interactive": '  # Chat (interactive)\n  r9s chat --model "$R9S_MODEL"',
        "cli.examples.chat_pipe": '  # Chat (pipe stdin)\n  echo "hello" | r9s chat --model "$R9S_MODEL"',
        "cli.examples.resume": "  # Resume a session\n  r9s chat resume",
        "cli.examples.bots": '  # Bots\n  r9s bot create mybot --model "$R9S_MODEL" --system-prompt "You are a helpful assistant"\n  r9s chat --bot mybot\n  r9s bot list',
        "cli.examples.run": '  # Run an app via r9s\n  r9s run $app --model "$R9S_MODEL"\n  # Supported apps: claude-code, cc',
        "cli.examples.configure": "  # Configure an app\n  r9s set $app\n  r9s reset $app\n  # Supported apps: claude-code, cc",
        "cli.examples.more": "Run 'r9s -h' to see all options.",
        "chat.title": "r9s chat",
        "chat.base_url": "base_url",
        "chat.model": "model",
        "chat.system_prompt_set": "system_prompt: (set)",
        "chat.extensions": "extensions",
        "chat.commands.title": "Commands:",
        "chat.commands.exit": "  /exit   Exit",
        "chat.commands.clear": "  /clear  Clear session history (does not delete history-file)",
        "chat.commands.help": "  /help   Show help",
        "chat.prompt.user": "You> ",
        "chat.prompt.assistant": "Assistant> ",
        "chat.msg.history_cleared": "Session history cleared.",
        "chat.err.unknown_command": "Unknown command: {cmd} (try /help)",
        "chat.err.missing_api_key": "Missing API key: set R9S_API_KEY or pass --api-key",
        "chat.err.missing_model": "Missing model: set R9S_MODEL or pass --model",
        "chat.err.history_not_json": "History file is not valid JSON: {path} ({err})",
        "chat.err.history_not_array": "History file must be a JSON array: {path}",
        "chat.err.ext_load_file": "Failed to load extension file: {path}",
        "chat.err.ext_contract": "Extension must provide one of: register(registry) / get_extension() / EXTENSION / extension",
        "chat.err.resume_requires_tty": "Resume requires an interactive TTY (no stdin piping).",
        "chat.resume.none": "No saved sessions found in: {dir}",
        "chat.resume.select": "Select a session to resume (enter number): ",
        "chat.resume.invalid": "Invalid selection, try again.",
        "set.select_tool": "Select tool to configure",
        "set.available_models": "Available models from API:",
        "set.select_model": "Select ANTHROPIC_MODEL",
        "set.select_small_model": "Select ANTHROPIC_SMALL_FAST_MODEL",
        "set.small_model_option_same": "Use same as main model ({model})",
        "set.small_model_option_list": "Select from model list",
        "set.small_model_option_manual": "Enter manually",
        "set.select_small_model_from_list": "Select small model",
        "set.enter_model": "Enter model name: ",
        "set.enter_model_empty": "Model name cannot be empty. Enter model name: ",
        "set.enter_small_model": "Enter small model name: ",
        "set.enter_small_model_empty": "Model name cannot be empty. Enter small model name: ",
        "set.summary_header": "\nConfiguration summary:",
        "set.summary_tool": "- Tool: {tool}",
        "set.summary_config_file": "- Config file: {path}",
        "set.summary_base_url": "- Base URL: {url}",
        "set.summary_main_model": "- Main Model: {model}",
        "set.summary_small_model": "- Small/Fast Model: {model}",
        "set.summary_api_key": "- API key: {apikey}",
        "set.confirm_apply": "Apply this configuration?",
        "set.cancelled": "Cancelled.",
        "set.success_written": "Configuration written to: {path}",
        "set.success_backup": "Backup saved to: {path}",
    },
    "zh-CN": {
        "cli.title": "r9s CLI",
        "cli.tagline": "与 r9s 对话、管理 bot，或配置本地开发工具接入 r9s。",
        "cli.examples.title": "常用用法示例：",
        "cli.examples.chat_interactive": '  # 对话（交互）\n  r9s chat --model "$R9S_MODEL"',
        "cli.examples.chat_pipe": '  # 对话（stdin 管道）\n  echo "hello" | r9s chat --model "$R9S_MODEL"',
        "cli.examples.resume": "  # 恢复对话\n  r9s chat resume",
        "cli.examples.bots": '  # Bots\n  r9s bot create mybot --model "$R9S_MODEL" --system-prompt "你是一个严谨的助手"\n  r9s chat --bot mybot\n  r9s bot list',
        "cli.examples.run": '  # 通过 r9s 启动应用\n  r9s run $app --model "$R9S_MODEL"\n  # 当前支持：claude-code, cc',
        "cli.examples.configure": "  # 配置应用\n  r9s set $app\n  r9s reset $app\n  # 当前支持：claude-code, cc",
        "cli.examples.more": "运行 'r9s -h' 查看全部选项。",
        "chat.title": "r9s chat",
        "chat.base_url": "base_url",
        "chat.model": "model",
        "chat.system_prompt_set": "system_prompt：（已设置）",
        "chat.extensions": "extensions",
        "chat.commands.title": "快捷命令：",
        "chat.commands.exit": "  /exit   退出",
        "chat.commands.clear": "  /clear  清空本次会话历史（不删除 history-file）",
        "chat.commands.help": "  /help   帮助",
        "chat.prompt.user": "You> ",
        "chat.prompt.assistant": "Assistant> ",
        "chat.msg.history_cleared": "已清空本次会话历史。",
        "chat.err.unknown_command": "未知命令: {cmd}（可用 /help）",
        "chat.err.missing_api_key": "缺少 API key：请设置 R9S_API_KEY 或传入 --api-key",
        "chat.err.missing_model": "缺少 model：请设置 R9S_MODEL 或传入 --model",
        "chat.err.history_not_json": "history 文件不是合法 JSON: {path} ({err})",
        "chat.err.history_not_array": "history 文件必须是 JSON array: {path}",
        "chat.err.ext_load_file": "无法加载扩展文件: {path}",
        "chat.err.ext_contract": "扩展必须提供 register(registry) / get_extension() / EXTENSION / extension 之一",
        "chat.err.resume_requires_tty": "resume 需要交互式终端（不能通过 stdin 管道）。",
        "chat.resume.none": "在此目录未找到可恢复会话: {dir}",
        "chat.resume.select": "选择要恢复的会话（输入编号）：",
        "chat.resume.invalid": "选择无效，请重试。",
        "set.select_tool": "选择要配置的工具",
        "set.available_models": "API 可用模型：",
        "set.select_model": "选择 ANTHROPIC_MODEL",
        "set.select_small_model": "选择 ANTHROPIC_SMALL_FAST_MODEL",
        "set.small_model_option_same": "使用与主模型相同 ({model})",
        "set.small_model_option_list": "从模型列表选择",
        "set.small_model_option_manual": "手动输入",
        "set.select_small_model_from_list": "选择小模型",
        "set.enter_model": "请输入模型名称：",
        "set.enter_model_empty": "模型名称不能为空，请重新输入：",
        "set.enter_small_model": "请输入小模型名称：",
        "set.enter_small_model_empty": "模型名称不能为空，请重新输入：",
        "set.summary_header": "\n配置摘要：",
        "set.summary_tool": "- 工具：{tool}",
        "set.summary_config_file": "- 配置文件：{path}",
        "set.summary_base_url": "- Base URL：{url}",
        "set.summary_main_model": "- 主模型：{model}",
        "set.summary_small_model": "- 小/快速模型：{model}",
        "set.summary_api_key": "- API key：{apikey}",
        "set.confirm_apply": "应用此配置？",
        "set.cancelled": "已取消。",
        "set.success_written": "配置已写入：{path}",
        "set.success_backup": "备份已保存：{path}",
    },
}


def t(key: str, lang: str, **kwargs: object) -> str:
    table = _STRINGS.get(lang) or _STRINGS["en"]
    template = table.get(key) or _STRINGS["en"].get(key) or key
    try:
        return template.format(**kwargs)
    except Exception:
        return template
