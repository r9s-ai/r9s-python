from __future__ import annotations

import base64
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

import streamlit as st

from r9s.sdk import R9S
from r9s.agents.local_store import LocalAgentStore, load_agent, load_version, save_agent
from r9s.agents.template import render as render_agent_template
from r9s.skills.loader import format_skills_context, load_skills
from r9s.errors import R9SError


def _format_api_error(exc: Exception) -> str:
    """Format API error with detailed information when available."""
    if isinstance(exc, R9SError):
        parts = [f"Request failed (HTTP {exc.status_code})"]
        # Try to get detailed error info
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
            # Show raw body if no structured error data
            parts.append(f"Details: {exc.body[:500]}")
        return "\n".join(parts)
    return f"Request failed: {exc}"


@dataclass
class AppConfig:
    api_key: str
    base_url: str
    model: str


def _get_env_default(name: str, default: str = "") -> str:
    value = st.session_state.get(name)
    if isinstance(value, str) and value.strip():
        return value.strip()
    import os

    return os.getenv(name, default).strip()


def _render_config() -> Optional[AppConfig]:
    with st.sidebar:
        # Logo and title
        st.markdown(
            """
            <div class="logo-container">
                <img src="https://routetokens.com/logo/logo.svg" alt="r9s logo">
                <span class="logo-text">r9s Web</span>
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.caption("AI-powered Agents, Chat & Image Generation")
        api_key = st.text_input(
            "R9S_API_KEY",
            value=_get_env_default("R9S_API_KEY"),
            type="password",
        )
        base_url = st.text_input(
            "R9S_BASE_URL",
            value=_get_env_default("R9S_BASE_URL", "https://api.r9s.ai/v1"),
        )
        model = st.text_input("R9S_MODEL", value=_get_env_default("R9S_MODEL", ""))

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


def _r9s_client(cfg: AppConfig) -> R9S:
    return R9S(api_key=cfg.api_key, server_url=cfg.base_url)


def _init_chat_state() -> None:
    if "chat_messages" not in st.session_state:
        st.session_state["chat_messages"] = []


def _as_text(content: Any) -> str:
    if content is None:
        return ""
    if isinstance(content, str):
        return content
    try:
        import json

        return json.dumps(content, ensure_ascii=False)
    except Exception:
        return str(content)


def _render_agents_page() -> None:
    st.header("Agents")

    store = LocalAgentStore()
    agents = store.list()
    names = [a.name for a in agents]

    c1, c2 = st.columns(2)
    with c1:
        st.subheader("Create Agent")
        new_name = st.text_input("name", key="agent_new_name")
        new_model = st.text_input("model", key="agent_new_model")
        new_provider = st.text_input("provider", value="r9s", key="agent_new_provider")
        new_desc = st.text_input("description", key="agent_new_desc")
        new_instructions = st.text_area("instructions", height=220, key="agent_new_inst")
        new_skills_raw = st.text_input("skills (comma-separated, optional)", key="agent_new_skills")
        if st.button("Create", type="primary", key="agent_create_btn"):
            if not new_name.strip():
                st.error("name is required")
            elif not new_model.strip():
                st.error("model is required")
            elif not new_instructions.strip():
                st.error("instructions is required")
            else:
                skills = [s.strip() for s in new_skills_raw.split(",") if s.strip()]
                created = store.create(
                    new_name.strip(),
                    instructions=new_instructions.strip(),
                    model=new_model.strip(),
                    provider=new_provider.strip() or "r9s",
                    description=new_desc.strip(),
                    change_reason="created via web",
                    skills=skills,
                )
                st.success(f"Created: {created.name} (version {created.current_version})")
                st.rerun()

    with c2:
        st.subheader("Manage Agents")
        if not names:
            st.info("No local agents found (default directory: ~/.r9s/agents).")
            return

        selected = st.selectbox("Select Agent", options=names, key="agent_selected")
        agent = load_agent(selected)
        version = load_version(selected, agent.current_version)

        st.markdown(f"- current_version: `{agent.current_version}`")
        st.markdown(f"- model: `{version.model}`")
        st.markdown(f"- provider: `{version.provider}`")

        st.divider()
        inst = st.text_area("instructions (saving creates a new version)", value=version.instructions, height=260)
        bump = st.checkbox("bump version (default: true)", value=True)
        change_reason = st.text_input("change_reason (optional)", value="updated via web")

        skills_text = ", ".join(version.skills or [])
        skills_raw = st.text_input("skills (comma-separated, optional)", value=skills_text)

        c2a, c2b = st.columns(2)
        with c2a:
            if st.button("Save", type="primary"):
                skills = [s.strip() for s in skills_raw.split(",") if s.strip()]
                store.update(
                    selected,
                    instructions=inst,
                    model=None,
                    provider=None,
                    change_reason=change_reason,
                    bump=bump,
                    skills=skills,
                )
                st.success("Updated")
                st.rerun()
        with c2b:
            if st.button("Delete Agent", type="secondary"):
                from r9s.agents.local_store import delete_agent

                delete_agent(selected)
                st.success("Deleted")
                st.rerun()

        st.divider()
        st.subheader("Rollback Version")
        versions = store.list_versions(selected)
        version_ids = [v.version for v in versions]
        rollback_to = st.selectbox("Target version", options=version_ids, index=0)
        if st.button("Set as current_version"):
            agent.current_version = rollback_to
            save_agent(agent)
            st.success(f"Rolled back to {rollback_to}")
            st.rerun()


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


def _render_chat_page(cfg: AppConfig) -> None:
    st.header("Chat")
    _init_chat_state()

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
            st.markdown(_as_text(content))

    upload = st.file_uploader("Optional: Upload an image for this message", type=["png", "jpg", "jpeg", "webp", "gif"])
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
            with _r9s_client(cfg) as r9s:
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
                        assistant_text = _as_text(res.choices[0].message.content)
                    placeholder.markdown(assistant_text or "")
        except Exception as exc:
            st.error(_format_api_error(exc))
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


def _render_images_page(cfg: AppConfig) -> None:
    st.header("Image Generation")

    prompt = st.text_area("Prompt", height=120)

    # Row 1: Basic options
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        n = st.number_input("n", min_value=1, max_value=10, value=1, step=1)
    with col2:
        size = st.selectbox(
            "size",
            options=["1024x1024", "1024x1536", "1536x1024", "512x512", "256x256", "auto"],
            index=0,
        )
    with col3:
        quality = st.selectbox(
            "quality",
            options=["(default)", "standard", "hd", "low", "medium", "high"],
            index=0,
        )
    with col4:
        image_model = st.text_input("model (optional)", value=_get_env_default("R9S_IMAGE_MODEL", ""))

    # Row 2: Additional options
    col5, col6, col7, col8 = st.columns(4)
    with col5:
        style = st.selectbox(
            "style (DALL-E 3)",
            options=["(default)", "vivid", "natural"],
            index=0,
        )
    with col6:
        response_format = st.selectbox(
            "response_format",
            options=["(auto)", "url", "b64_json"],
            index=0,
            help="GPT image models don't support this parameter",
        )
    with col7:
        seed_input = st.text_input("seed (optional)", value="", help="Random seed for reproducibility")
    with col8:
        negative_prompt = st.text_input("negative_prompt (optional)", value="", help="For Qwen/Stability models")

    if st.button("Generate", type="primary"):
        if not prompt.strip():
            st.error("Prompt is required")
            return
        model: Optional[str] = image_model.strip() or None

        # Build kwargs - only include parameters that are set
        kwargs: Dict[str, Any] = {
            "prompt": prompt.strip(),
            "n": int(n),
        }
        if model:
            kwargs["model"] = model
        if size != "auto":
            kwargs["size"] = size
        if quality != "(default)":
            kwargs["quality"] = quality

        # Model-specific parameter filtering
        # GPT image models don't support: response_format, style, seed, negative_prompt
        is_gpt_image = model and model.lower().startswith("gpt-image")

        if style != "(default)" and not is_gpt_image:
            kwargs["style"] = style

        if response_format != "(auto)" and not is_gpt_image:
            kwargs["response_format"] = response_format

        if seed_input.strip() and not is_gpt_image:
            try:
                kwargs["seed"] = int(seed_input.strip())
            except ValueError:
                st.error("seed must be an integer")
                return

        if negative_prompt.strip() and not is_gpt_image:
            kwargs["negative_prompt"] = negative_prompt.strip()

        with st.spinner("Generating..."):
            try:
                with _r9s_client(cfg) as r9s:
                    res = r9s.images.create(**kwargs)
            except Exception as exc:
                st.error(_format_api_error(exc))
                return

        # Store generated images in session state for persistence across reruns
        st.session_state["generated_images"] = []
        st.session_state["generated_urls"] = []
        for i, img in enumerate(res.data):
            url = getattr(img, "url", None)
            b64_json = getattr(img, "b64_json", None)
            image_data = None
            image_url = None

            if url:
                image_url = url
                # Download for potential editing
                try:
                    import urllib.request
                    with urllib.request.urlopen(url, timeout=30) as resp:
                        image_data = resp.read()
                except Exception:
                    pass
            elif b64_json:
                image_data = base64.b64decode(b64_json)

            revised = getattr(img, "revised_prompt", None)
            st.session_state["generated_images"].append({
                "index": i,
                "data": image_data,
                "url": image_url,
                "model": model,
                "revised_prompt": revised,
            })

    # Display generated images from session state (persists across reruns)
    if st.session_state.get("generated_images"):
        st.divider()
        st.subheader("Generated Images")
        for img_info in st.session_state["generated_images"]:
            st.markdown(f"**Result {img_info['index'] + 1}**")
            if img_info.get("data"):
                st.image(img_info["data"])
            elif img_info.get("url"):
                st.image(img_info["url"])
            if img_info.get("url"):
                st.code(img_info["url"])
            if img_info.get("revised_prompt"):
                st.caption(f"revised_prompt: {img_info['revised_prompt']}")

    # Show edit section if we have generated images
    if st.session_state.get("generated_images") and any(img.get("data") for img in st.session_state["generated_images"]):
        st.divider()
        st.subheader("Edit Generated Image")

        images = st.session_state["generated_images"]
        if len(images) > 1:
            edit_idx = st.selectbox(
                "Select image to edit",
                options=list(range(len(images))),
                format_func=lambda x: f"Result {x + 1}",
                key="edit_image_select",
            )
        else:
            edit_idx = 0

        edit_prompt = st.text_area(
            "Edit prompt",
            placeholder="Describe what changes you want to make...",
            height=100,
            key="edit_prompt",
        )

        if st.button("Edit Image", type="primary", key="edit_btn"):
            if not edit_prompt.strip():
                st.error("Edit prompt is required")
            else:
                selected_img = images[edit_idx]
                edit_kwargs: Dict[str, Any] = {
                    "image": {
                        "file_name": "image.png",
                        "content": selected_img["data"],
                        "content_type": "image/png",
                    },
                    "prompt": edit_prompt.strip(),
                }
                if selected_img.get("model"):
                    edit_kwargs["model"] = selected_img["model"]

                with st.spinner("Editing..."):
                    try:
                        with _r9s_client(cfg) as r9s:
                            edit_res = r9s.images.edit(**edit_kwargs)
                    except Exception as exc:
                        st.error(_format_api_error(exc))
                        return

                for j, edited_img in enumerate(edit_res.data):
                    st.subheader(f"Edited Result {j + 1}")
                    edited_url = getattr(edited_img, "url", None)
                    edited_b64 = getattr(edited_img, "b64_json", None)
                    edited_data = None
                    if edited_url:
                        st.image(edited_url)
                        st.code(edited_url)
                        try:
                            import urllib.request
                            with urllib.request.urlopen(edited_url, timeout=30) as resp:
                                edited_data = resp.read()
                        except Exception:
                            pass
                    elif edited_b64:
                        edited_data = base64.b64decode(edited_b64)
                        st.image(edited_data)

                    # Replace the original with edited version for further edits
                    if edited_data:
                        st.session_state["generated_images"][edit_idx] = {
                            "index": edit_idx,
                            "data": edited_data,
                            "model": selected_img.get("model"),
                        }


def _apply_custom_styles() -> None:
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

        /* Sidebar styling */
        [data-testid="stSidebar"] {
            background: linear-gradient(180deg, #1e1e2e 0%, #181825 100%);
        }

        /* Input fields */
        .stTextInput > div > div > input,
        .stTextArea > div > div > textarea {
            border-radius: 8px;
            border: 1px solid #3f3f5a;
            background-color: #1e1e2e;
        }
        .stTextInput > div > div > input:focus,
        .stTextArea > div > div > textarea:focus {
            border-color: #6366f1;
            box-shadow: 0 0 0 2px rgba(99, 102, 241, 0.2);
        }

        /* Select boxes */
        .stSelectbox > div > div {
            border-radius: 8px;
        }

        /* Cards/containers */
        .stSubheader {
            padding-top: 1rem;
            border-bottom: 1px solid #3f3f5a;
            padding-bottom: 0.5rem;
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

        /* Divider styling */
        hr {
            border-color: #3f3f5a;
            opacity: 0.5;
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


def main() -> None:
    st.set_page_config(
        page_title="r9s Web",
        page_icon="https://routetokens.com/logo/logo.svg",
        layout="wide",
    )
    _apply_custom_styles()

    cfg = _render_config()
    if cfg is None:
        st.stop()

    with st.sidebar:
        page = st.radio("Page", options=["Chat", "Agents", "Image Generation"], index=0)

    if page == "Chat":
        _render_chat_page(cfg)
        return
    if page == "Agents":
        _render_agents_page()
        return
    if page == "Image Generation":
        _render_images_page(cfg)
        return


if __name__ == "__main__":
    main()
