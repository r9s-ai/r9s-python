from __future__ import annotations

import argparse
import importlib.util
import os
import socket
import subprocess
import sys
from pathlib import Path
from typing import Iterable

from r9s.cli_tools.i18n import resolve_lang, t


def _require_streamlit(lang: str) -> None:
    if importlib.util.find_spec("streamlit") is None:
        raise SystemExit(t("web.err.streamlit_missing", lang))


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


def _allocate_ephemeral_port(host: str, lang: str) -> int:
    for family, socktype, proto, sockaddr in _iter_bind_targets(host, 0):
        with socket.socket(family, socktype, proto) as s:
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            s.bind(sockaddr)
            return int(s.getsockname()[1])
    raise SystemExit(t("web.err.bind_host_failed", lang, host=host))


def _pick_port(host: str, preferred_port: int, *, auto_port: bool, lang: str) -> int:
    if preferred_port < 0 or preferred_port > 65535:
        raise SystemExit(t("web.err.port_out_of_range", lang))

    if preferred_port == 0:
        port = _allocate_ephemeral_port(host, lang)
        print(t("web.msg.auto_port_allocated", lang, port=port), file=sys.stderr)
        return port

    if not auto_port:
        return preferred_port

    if _is_port_available(host, preferred_port):
        return preferred_port

    for port in range(preferred_port + 1, preferred_port + 101):
        if _is_port_available(host, port):
            print(t("web.msg.port_switched", lang, preferred_port=preferred_port, port=port), file=sys.stderr)
            return port

    raise SystemExit(t("web.err.port_range_exhausted", lang, preferred_port=preferred_port))


def handle_web(args: argparse.Namespace) -> None:
    lang = resolve_lang(getattr(args, "lang", None))
    _require_streamlit(lang)

    from r9s.web import app as web_app

    app_path = Path(web_app.__file__).resolve()

    host = str(getattr(args, "host", "127.0.0.1"))
    preferred_port = int(getattr(args, "port", 8501))
    auto_port = bool(getattr(args, "auto_port", True))
    port = _pick_port(host, preferred_port, auto_port=auto_port, lang=lang)

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
