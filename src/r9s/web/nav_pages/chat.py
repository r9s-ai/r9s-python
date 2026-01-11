from __future__ import annotations

import base64
from typing import Any, Dict, List, Optional, Tuple

import streamlit as st

from r9s.agents.local_store import LocalAgentStore
from r9s.agents.template import render as render_agent_template
from r9s.skills.loader import format_skills_context, load_skills
from r9s.web.common import AppConfig, as_text, format_api_error, init_chat_state, r9s_client


def _build_system_prompt_from_agent(
    agent_name: str, variables: Dict[str, str]
) -> Tuple[str, List[str]]:
    store = LocalAgentStore()
    agent = store.get_agent(agent_name)
    version = store.get_version(agent_name, agent.current_version)
    base = render_agent_template(version.instructions, variables)
    skills = list(version.skills) if version.skills else []
    loaded = load_skills(skills, warn_fn=lambda msg: st.warning(str(msg)))
    skills_ctx = format_skills_context(loaded)
    if skills_ctx:
        base = f"{base}\n{skills_ctx}"
    return base, skills


def run(cfg: AppConfig) -> None:
    st.header("Chat")
    init_chat_state()

    with st.sidebar:
        st.subheader("Chat Settings")
        use_stream = st.checkbox("Stream output", value=True)
        agent_names = [a.name for a in LocalAgentStore().list()]
        agent_name = st.selectbox("Use Agent (optional)", options=["(none)"] + agent_names)
        vars_raw = st.text_area("Agent variables (JSON, optional)", value="{}", height=100)

    system_prompt: Optional[str] = None
    if agent_name != "(none)":
        try:
            import json

            variables_obj = json.loads(vars_raw or "{}")
            if not isinstance(variables_obj, dict):
                raise ValueError("variables must be a JSON object")
            variables = {str(k): str(v) for k, v in variables_obj.items()}
            system_prompt, _skills = _build_system_prompt_from_agent(agent_name, variables)
        except Exception as exc:
            st.sidebar.error(f"Failed to parse Agent variables: {exc}")
            return

    for msg in st.session_state["chat_messages"]:
        role = msg.get("role", "assistant")
        content = msg.get("content")
        with st.chat_message(role):
            st.markdown(as_text(content))

    upload = st.file_uploader(
        "Optional: Upload an image for this message", type=["png", "jpg", "jpeg", "webp", "gif"]
    )
    prompt = st.chat_input("Enter message...")
    if not prompt:
        return

    user_msg: Dict[str, Any]
    if upload is not None:
        data = upload.getvalue()
        mime = upload.type or "image/png"
        b64 = base64.b64encode(data).decode("ascii")
        url = f"data:{mime};base64,{b64}"
        user_msg = {
            "role": "user",
            "content": [
                {"type": "text", "text": prompt},
                {"type": "image_url", "image_url": {"url": url, "detail": "auto"}},
            ],
        }
    else:
        user_msg = {"role": "user", "content": prompt}

    st.session_state["chat_messages"].append(user_msg)
    with st.chat_message("user"):
        st.markdown(prompt)

    messages: List[Dict[str, Any]] = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    messages.extend(st.session_state["chat_messages"])

    with st.chat_message("assistant"):
        placeholder = st.empty()
        assistant_text = ""
        try:
            with r9s_client(cfg) as r9s:
                if use_stream:
                    stream = r9s.chat.create(model=cfg.model, messages=messages, stream=True)
                    for event in stream:
                        if not getattr(event, "choices", None):
                            continue
                        delta = event.choices[0].delta
                        piece = getattr(delta, "content", None) or ""
                        if not piece:
                            continue
                        assistant_text += piece
                        placeholder.markdown(assistant_text)
                else:
                    res = r9s.chat.create(model=cfg.model, messages=messages, stream=False)
                    if res.choices and res.choices[0].message:
                        assistant_text = as_text(res.choices[0].message.content)
                    placeholder.markdown(assistant_text or "")
        except Exception as exc:
            st.error(format_api_error(exc))
            return

    st.session_state["chat_messages"].append({"role": "assistant", "content": assistant_text})

    c1, c2 = st.columns(2)
    with c1:
        if st.button("Clear chat", type="secondary"):
            st.session_state["chat_messages"] = []
            st.rerun()
    with c2:
        if system_prompt and st.button("View system prompt"):
            st.code(system_prompt)

