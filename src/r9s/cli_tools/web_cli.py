from __future__ import annotations

import argparse
import importlib.util
import os
import subprocess
import sys
from pathlib import Path


def _require_streamlit() -> None:
    if importlib.util.find_spec("streamlit") is None:
        raise SystemExit(
            "未安装 Web UI 依赖：streamlit。\n"
            "请执行：pip install 'r9s[web]'"
        )


def handle_web(args: argparse.Namespace) -> None:
    _require_streamlit()

    from r9s.web import app as web_app

    app_path = Path(web_app.__file__).resolve()

    cmd = [
        sys.executable,
        "-m",
        "streamlit",
        "run",
        str(app_path),
        "--server.address",
        str(getattr(args, "host", "127.0.0.1")),
        "--server.port",
        str(getattr(args, "port", 8501)),
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

