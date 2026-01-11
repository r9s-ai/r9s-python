from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any, Optional

import streamlit as st

from r9s.errors import R9SError
from r9s.sdk import R9S


def format_api_error(exc: Exception) -> str:
    """Format API error with detailed information when available."""
    if isinstance(exc, R9SError):
        parts = [f"Request failed (HTTP {exc.status_code})"]
        if hasattr(exc, "data") and hasattr(exc.data, "error"):
            err = exc.data.error
            if hasattr(err, "message") and err.message:
                parts.append(f"Message: {err.message}")
            if hasattr(err, "type") and err.type:
                parts.append(f"Type: {err.type}")
            if hasattr(err, "code") and err.code:
                parts.append(f"Code: {err.code}")
            if hasattr(err, "param") and err.param:
                parts.append(f"Param: {err.param}")
        elif exc.body:
            parts.append(f"Details: {exc.body[:500]}")
        return "\n".join(parts)
    return f"Request failed: {exc}"


@dataclass
class AppConfig:
    api_key: str
    base_url: str
    model: str


def get_env_default(name: str, default: str = "") -> str:
    value = st.session_state.get(name)
    if isinstance(value, str) and value.strip():
        return value.strip()
    return os.getenv(name, default).strip()


def render_config() -> Optional[AppConfig]:
    with st.sidebar:
        st.markdown(
            """
            <div class="logo-container">
                <img src="https://routetokens.com/logo/logo.svg" alt="r9s logo">
                <span class="logo-text">r9s Web</span>
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.caption("AI-powered Agents, Chat, Image & Audio")
        api_key = st.text_input(
            "R9S_API_KEY",
            value=get_env_default("R9S_API_KEY"),
            type="password",
        )
        base_url = st.text_input(
            "R9S_BASE_URL",
            value=get_env_default("R9S_BASE_URL", "https://api.r9s.ai/v1"),
        )
        model = st.text_input("R9S_MODEL", value=get_env_default("R9S_MODEL", ""))

        st.session_state["R9S_API_KEY"] = api_key
        st.session_state["R9S_BASE_URL"] = base_url
        st.session_state["R9S_MODEL"] = model

        if not api_key.strip():
            st.warning("Please set R9S_API_KEY in the sidebar (or set environment variable).")
            return None
        if not base_url.strip():
            st.warning("Please set R9S_BASE_URL (or set environment variable).")
            return None
        if not model.strip():
            st.warning("Please set R9S_MODEL (or set environment variable).")
            return None
        return AppConfig(
            api_key=api_key.strip(),
            base_url=base_url.strip(),
            model=model.strip(),
        )


def r9s_client(cfg: AppConfig) -> R9S:
    return R9S(api_key=cfg.api_key, server_url=cfg.base_url)


def init_chat_state() -> None:
    if "chat_messages" not in st.session_state:
        st.session_state["chat_messages"] = []


def as_text(content: Any) -> str:
    if content is None:
        return ""
    if isinstance(content, str):
        return content
    try:
        import json

        return json.dumps(content, ensure_ascii=False)
    except Exception:
        return str(content)


def apply_custom_styles() -> None:
    """Apply custom CSS styles for a more polished look."""
    st.markdown(
        """
        <style>
        /* Import Google Font */
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

        /* Global font */
        html, body, [class*="css"] {
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
        }

        /* Headers styling */
        h1, h2, h3 {
            font-weight: 600 !important;
            letter-spacing: -0.02em;
        }

        /* Primary button styling */
        .stButton > button[kind="primary"] {
            background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%);
            border: none;
            font-weight: 500;
            transition: all 0.2s ease;
        }
        .stButton > button[kind="primary"]:hover {
            background: linear-gradient(135deg, #4f46e5 0%, #7c3aed 100%);
            box-shadow: 0 4px 12px rgba(99, 102, 241, 0.4);
        }

        /* Secondary button styling */
        .stButton > button[kind="secondary"] {
            border: 1px solid #6366f1;
            color: #6366f1;
            font-weight: 500;
        }

        /* Select boxes */
        .stSelectbox > div > div {
            border-radius: 8px;
        }

        /* Input fields - base styling */
        .stTextInput > div > div > input,
        .stTextArea > div > div > textarea {
            border-radius: 8px;
        }
        .stTextInput > div > div > input:focus,
        .stTextArea > div > div > textarea:focus {
            border-color: #6366f1;
            box-shadow: 0 0 0 2px rgba(99, 102, 241, 0.2);
        }

        /* Logo container */
        .logo-container {
            display: flex;
            align-items: center;
            gap: 12px;
            padding: 8px 0 16px 0;
        }
        .logo-container img {
            height: 36px;
            width: auto;
        }
        .logo-text {
            font-size: 1.5rem;
            font-weight: 700;
            background: linear-gradient(135deg, #6366f1 0%, #a855f7 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
        }

        /* Cards/containers */
        .stSubheader {
            padding-top: 1rem;
            padding-bottom: 0.5rem;
        }

        /* Dark mode specific styles */
        @media (prefers-color-scheme: dark) {
            [data-testid="stSidebar"] {
                background: linear-gradient(180deg, #1e1e2e 0%, #181825 100%);
            }
            .stTextInput > div > div > input,
            .stTextArea > div > div > textarea {
                border: 1px solid #3f3f5a;
                background-color: #1e1e2e;
            }
            .stSubheader {
                border-bottom: 1px solid #3f3f5a;
            }
            .logo-container img {
                filter: invert(1) brightness(2);
            }
            hr {
                border-color: #3f3f5a;
                opacity: 0.5;
            }
        }

        /* Light mode specific styles */
        @media (prefers-color-scheme: light) {
            [data-testid="stSidebar"] {
                background: linear-gradient(180deg, #f8f9fc 0%, #eef1f8 100%);
            }
            .stTextInput > div > div > input,
            .stTextArea > div > div > textarea {
                border: 1px solid #d1d5db;
                background-color: #ffffff;
            }
            .stSubheader {
                border-bottom: 1px solid #e5e7eb;
            }
            hr {
                border-color: #e5e7eb;
                opacity: 0.5;
            }
        }

        /* Image display */
        .stImage {
            border-radius: 12px;
            overflow: hidden;
        }

        /* Code blocks */
        .stCode {
            border-radius: 8px;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

