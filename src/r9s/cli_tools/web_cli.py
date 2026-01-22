from __future__ import annotations

import argparse
import importlib.util
import os
import socket
import subprocess
import sys
from pathlib import Path
from typing import Iterable


def _require_streamlit() -> None:
    if importlib.util.find_spec("streamlit") is None:
        raise SystemExit(
            "未安装 Web UI 依赖：streamlit。\n"
            "请执行：pip install 'r9s[web]'"
        )


def _iter_bind_targets(host: str, port: int) -> Iterable[tuple]:
    for family, socktype, proto, _, sockaddr in socket.getaddrinfo(
        host,
        port,
        type=socket.SOCK_STREAM,
    ):
        yield (family, socktype, proto, sockaddr)


def _is_port_available(host: str, port: int) -> bool:
    try:
        for family, socktype, proto, sockaddr in _iter_bind_targets(host, port):
            with socket.socket(family, socktype, proto) as s:
                s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                s.bind(sockaddr)
        return True
    except OSError:
        return False


def _allocate_ephemeral_port(host: str) -> int:
    for family, socktype, proto, sockaddr in _iter_bind_targets(host, 0):
        with socket.socket(family, socktype, proto) as s:
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            s.bind(sockaddr)
            return int(s.getsockname()[1])
    raise SystemExit(f"无法为 host={host!r} 分配可用端口，请使用 --host 指定一个可绑定的地址。")


def _pick_port(host: str, preferred_port: int, *, auto_port: bool) -> int:
    if preferred_port < 0 or preferred_port > 65535:
        raise SystemExit("--port 必须在 0..65535 范围内")

    if preferred_port == 0:
        port = _allocate_ephemeral_port(host)
        print(f"已自动分配可用端口：{port}", file=sys.stderr)
        return port

    if not auto_port:
        return preferred_port

    if _is_port_available(host, preferred_port):
        return preferred_port

    for port in range(preferred_port + 1, preferred_port + 101):
        if _is_port_available(host, port):
            print(
                f"端口 {preferred_port} 已被占用，自动切换到 {port}（可用 --no-auto-port 禁用）",
                file=sys.stderr,
            )
            return port

    raise SystemExit(
        f"端口 {preferred_port} 已被占用，且后续 100 个端口都不可用；请使用 --port 指定。"
    )


def handle_web(args: argparse.Namespace) -> None:
    _require_streamlit()

    from r9s.web import app as web_app

    app_path = Path(web_app.__file__).resolve()

    host = str(getattr(args, "host", "127.0.0.1"))
    preferred_port = int(getattr(args, "port", 8501))
    auto_port = bool(getattr(args, "auto_port", True))
    port = _pick_port(host, preferred_port, auto_port=auto_port)

    cmd = [
        sys.executable,
        "-m",
        "streamlit",
        "run",
        str(app_path),
        "--server.address",
        host,
        "--server.port",
        str(port),
        "--server.headless",
        "false" if getattr(args, "open_browser", False) else "true",
        "--browser.gatherUsageStats",
        "false",
    ]

    env = os.environ.copy()
    api_key = getattr(args, "api_key", None)
    base_url = getattr(args, "base_url", None)
    lang = getattr(args, "lang", None)
    model = getattr(args, "model", None)

    if api_key:
        env["R9S_API_KEY"] = api_key
    if base_url:
        env["R9S_BASE_URL"] = base_url
    if lang:
        env["R9S_LANG"] = lang
    if model:
        env["R9S_MODEL"] = model

    raise SystemExit(subprocess.call(cmd, env=env))
