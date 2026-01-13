from __future__ import annotations

import base64
from typing import Any, Dict, List, Optional, Tuple, cast

import streamlit as st

from r9s.agents.local_store import LocalAgentStore
from r9s.agents.template import render as render_agent_template
from r9s.skills.loader import format_skills_context, load_skills
from r9s.models.message import MessageTypedDict
from r9s.web.common import AppConfig, as_text, format_api_error, init_chat_state, r9s_client


@st.cache_data(ttl=60)
def _get_agent_names() -> List[str]:
    """Cache agent names to avoid repeated disk reads during reruns."""
    return [a.name for a in LocalAgentStore().list()]


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

    # Initialize stop flag in session state
    if "stop_generation" not in st.session_state:
        st.session_state["stop_generation"] = False
    if "is_generating" not in st.session_state:
        st.session_state["is_generating"] = False
    if "generation_started" not in st.session_state:
        st.session_state["generation_started"] = False

    # Check if we're in the middle of generation (after rerun)
    # Skip sidebar processing to avoid redundant work
    generation_in_progress = st.session_state.get("generation_started", False)

    # Only process sidebar when not generating (optimization for rerun)
    if not generation_in_progress:
        with st.sidebar:
            st.subheader("Chat Settings")
            use_stream = st.checkbox("Stream output", value=True, key="chat_use_stream")
            agent_names = _get_agent_names()
            agent_name = st.selectbox(
                "Use Agent (optional)",
                options=["(none)"] + agent_names,
                key="chat_agent_name"
            )
            vars_raw = st.text_area(
                "Agent variables (JSON, optional)",
                value="{}",
                height=100,
                key="chat_vars_raw"
            )

            st.divider()
            if st.button(
                ":material/delete_forever: Clear Chat",
                type="secondary",
                use_container_width=True,
                help="Clear all chat history"
            ):
                st.session_state["chat_messages"] = []
                st.rerun()

        # Store sidebar values in session state for use during generation
        st.session_state["_chat_use_stream"] = use_stream
        st.session_state["_chat_agent_name"] = agent_name
        st.session_state["_chat_vars_raw"] = vars_raw
    else:
        # During generation, restore values from session state
        use_stream = st.session_state.get("_chat_use_stream", True)
        agent_name = st.session_state.get("_chat_agent_name", "(none)")
        vars_raw = st.session_state.get("_chat_vars_raw", "{}")

    # Build system prompt only when not generating (it's already saved in pending_messages)
    system_prompt: Optional[str] = None
    if not generation_in_progress and agent_name != "(none)":
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

    def render_message_content(content: Any) -> None:
        if isinstance(content, list):
            for item in content:
                if not isinstance(item, dict):
                    st.markdown(as_text(item))
                    continue
                ctype = item.get("type")
                if ctype == "image_url" and isinstance(item.get("image_url"), dict):
                    url = item["image_url"].get("url")
                    if url:
                        st.image(url, caption=item["image_url"].get("alt"))
                    else:
                        st.markdown(as_text(item))
                elif ctype == "text":
                    text_val = item.get("text", "")
                    if text_val.startswith("📄 **") and "```" in text_val:
                        header = text_val.split("```", 1)[0].strip()
                        st.markdown(f"{header}\n(Content sent to model)")
                    else:
                        st.markdown(text_val)
                else:
                    st.markdown(as_text(item))
        else:
            st.markdown(as_text(content))

    for msg in st.session_state["chat_messages"]:
        role = msg.get("role", "assistant")
        content = msg.get("content")
        with st.chat_message(role):
            render_message_content(content)

    # Supported file types for upload (limited to text-like files and images)
    image_types = ["png", "jpg", "jpeg", "webp", "gif", "bmp", "svg", "ico"]
    doc_types = ["txt", "md", "csv", "json", "xml", "html", "log"]
    code_types = ["py", "js", "ts", "java", "c", "cpp", "go", "rs", "rb", "sh"]
    supported_types = image_types + doc_types + code_types

    placeholder = "Type a message or drop files (images, text, code)..."

    # Callback functions for buttons
    def stop_generation() -> None:
        """Stop the ongoing generation"""
        st.session_state["stop_generation"] = True
        st.toast("Stopping generation...", icon="⏹️")

    def recall_last_message() -> None:
        """Recall the last pair of user-assistant messages"""
        if len(st.session_state["chat_messages"]) >= 2:
            # Remove last assistant message and last user message
            st.session_state["chat_messages"].pop()
            st.session_state["chat_messages"].pop()
            st.toast("Recalled last message", icon="⏪")
            # Note: st.rerun() not needed here - Streamlit auto-reruns after on_click callback
        else:
            st.toast("No messages to recall", icon="⚠️")

    def resend_last_message() -> None:
        """Mark that we should resend the last message"""
        if st.session_state["chat_messages"]:
            st.session_state["resend_requested"] = True
        else:
            st.toast("No messages to resend", icon="⚠️")

    # Bottom-aligned input with buttons
    with st._bottom:
        cols = st.columns([1.2, 15, 1], vertical_alignment="bottom", gap="small")

        with cols[0]:
            # Left: Recall button (only when not generating)
            if not st.session_state["is_generating"]:
                st.button(
                    ":material/undo:",
                    on_click=recall_last_message,
                    help="Recall last message",
                    use_container_width=True,
                    key="recall_button"
                )
            else:
                # Show stop button during generation
                st.button(
                    ":material/stop:",
                    on_click=stop_generation,
                    help="Stop generation",
                    use_container_width=True,
                    key="stop_button",
                    type="primary"
                )

        with cols[1]:
            # Middle: Chat input with file upload support (disabled during generation)
            chat_input = st.chat_input(
                placeholder,
                accept_file="multiple",
                file_type=supported_types,
                key="chat_input_with_files",
                disabled=st.session_state["is_generating"]
            )

        with cols[2]:
            # Right: Resend button (only when not generating)
            if not st.session_state["is_generating"]:
                st.button(
                    ":material/refresh:",
                    on_click=resend_last_message,
                    help="Resend last message",
                    use_container_width=True,
                    key="resend_button"
                )
            else:
                # Empty placeholder to maintain layout
                st.empty()

    # Handle resend request
    resend_mode = False
    if st.session_state.get("resend_requested", False):
        st.session_state["resend_requested"] = False
        if st.session_state["chat_messages"]:
            # Remove last assistant message if exists
            if st.session_state["chat_messages"][-1].get("role") == "assistant":
                st.session_state["chat_messages"].pop()
            # Get the last user message to resend
            if st.session_state["chat_messages"] and st.session_state["chat_messages"][-1].get("role") == "user":
                # Will be processed below
                chat_input = st.session_state["chat_messages"][-1]
                # Don't remove it - keep it in history
                resend_mode = True
                st.toast("Resending...", icon="🔄")
            else:
                return
        else:
            return

    generation_started = st.session_state.get("generation_started", False)

    if not chat_input and not generation_started:
        return

    messages: List[MessageTypedDict] = []
    if not generation_started:
        # Handle both normal input and resend scenario
        user_msg: MessageTypedDict
        if isinstance(chat_input, dict) and "role" in chat_input:
            # This is a resend - chat_input is already a message dict
            user_msg = cast(MessageTypedDict, chat_input)
        else:
            # Normal input from chat_input widget - use getattr for type safety
            prompt: str = getattr(chat_input, "text", "") or ""
            files: list[Any] = list(getattr(chat_input, "files", None) or [])

            if files:
                content: List[Dict[str, Any]] = []
                if prompt:
                    content.append({"type": "text", "text": prompt})
                for upload in files:
                    ext = (upload.name.rsplit(".", 1)[-1] if "." in upload.name else "").lower()
                    if ext not in supported_types:
                        st.warning(f"Unsupported file type: {upload.name}; skipping.")
                        continue
                    if ext in image_types:
                        # Handle image files
                        data = upload.getvalue()
                        mime = upload.type or "image/png"
                        b64 = base64.b64encode(data).decode("ascii")
                        url = f"data:{mime};base64,{b64}"
                        content.append({"type": "image_url", "image_url": {"url": url, "detail": "auto"}})
                    else:
                        # Handle text/code/document files
                        raw_bytes = upload.getvalue()
                        text_content: str | None = None
                        encoding_used = "utf-8"

                        # Try UTF-8 first (most common)
                        try:
                            text_content = raw_bytes.decode("utf-8")
                        except UnicodeDecodeError:
                            pass

                        # Try other common encodings for HTML/XML files
                        if text_content is None:
                            for enc in ("utf-16", "gbk", "gb2312", "latin-1"):
                                try:
                                    text_content = raw_bytes.decode(enc)
                                    encoding_used = enc
                                    break
                                except (UnicodeDecodeError, LookupError):
                                    continue

                        # Fallback: decode with replacement characters
                        if text_content is None:
                            text_content = raw_bytes.decode("utf-8", errors="replace")
                            encoding_used = "utf-8 (lossy)"
                            st.warning(
                                f"File '{upload.name}' contains non-UTF-8 characters. "
                                "Some characters may display incorrectly."
                            )

                        file_text = f"📄 **{upload.name}**:\n```\n{text_content}\n```"
                        content.append({"type": "text", "text": file_text})
                user_msg = cast(MessageTypedDict, {"role": "user", "content": content})
            else:
                user_msg = cast(MessageTypedDict, {"role": "user", "content": prompt})

        # Only append message if it's not a resend (resend already has the message in history)
        if not resend_mode:
            st.session_state["chat_messages"].append(user_msg)
            with st.chat_message("user"):
                render_message_content(user_msg.get("content"))

        if system_prompt:
            messages.append(cast(MessageTypedDict, {"role": "system", "content": system_prompt}))
        messages.extend(cast(List[MessageTypedDict], st.session_state["chat_messages"]))

        # Set generating state and rerun to update UI (show stop button)
        st.session_state["stop_generation"] = False
        st.session_state["is_generating"] = True
        st.session_state["generation_started"] = True
        st.session_state["pending_messages"] = messages  # Save messages for next run
        st.rerun()

    # Now we're in the second run with updated UI; restore messages from session state
    messages = st.session_state.get("pending_messages", messages)
    st.session_state["is_generating"] = True

    with st.chat_message("assistant"):
        # Check if generation was stopped during previous run (before resetting partial content)
        if st.session_state.get("stop_generation", False):
            partial = st.session_state.get("current_assistant_partial", "")
            if partial:
                stopped_content = f"{partial}\n\n_Response stopped by user._"
            else:
                stopped_content = "_Response stopped by user._"
            st.markdown(stopped_content)
            st.session_state["chat_messages"].append({"role": "assistant", "content": stopped_content})
            # Reset states
            st.session_state["is_generating"] = False
            st.session_state["generation_started"] = False
            st.session_state["stop_generation"] = False
            st.session_state.pop("current_assistant_partial", None)
            st.session_state.pop("pending_messages", None)
            st.rerun()

        placeholder = st.empty()
        placeholder.markdown("_Thinking…_")
        st.session_state["current_assistant_partial"] = ""

        def send_request() -> Tuple[bool, str]:
            """Send request and return (completed, assistant_text)."""
            result_text = ""
            with r9s_client(cfg) as r9s:
                if use_stream:
                    stream = r9s.chat.create(model=cfg.model, messages=messages, stream=True)
                    for event in stream:
                        # Check stop flag
                        if st.session_state.get("stop_generation", False):
                            stop_suffix = "Response stopped by user."
                            partial = result_text or st.session_state.get("current_assistant_partial", "")
                            stopped_content = (
                                f"{partial}\n\n{stop_suffix}" if partial else stop_suffix
                            )
                            placeholder.markdown(stopped_content)
                            # Mark stopped content to avoid duplicate append
                            st.session_state["stopped_content_to_save"] = stopped_content
                            return False, result_text

                        if not getattr(event, "choices", None):
                            continue
                        delta = event.choices[0].delta
                        piece = getattr(delta, "content", None) or ""
                        if not piece:
                            continue
                        # Ensure piece is text (may come as list/other types)
                        if not isinstance(piece, str):
                            piece = as_text(piece)
                        result_text += piece
                        st.session_state["current_assistant_partial"] = result_text
                        placeholder.markdown(result_text)
                    # If stream ended but user requested stop, still record partial content
                    if st.session_state.get("stop_generation", False):
                        stop_suffix = "Response stopped by user."
                        partial = result_text or st.session_state.get("current_assistant_partial", "")
                        stopped_content = (
                            f"{partial}\n\n{stop_suffix}" if partial else stop_suffix
                        )
                        placeholder.markdown(stopped_content)
                        st.session_state["stopped_content_to_save"] = stopped_content
                        return False, result_text
                else:
                    res = r9s.chat.create(model=cfg.model, messages=messages, stream=False)
                    if res.choices and res.choices[0].message:
                        result_text = as_text(res.choices[0].message.content)
                    placeholder.markdown(result_text or "")
            return True, result_text

        try:
            completed, assistant_text = send_request()
            if not completed:
                # Generation was stopped (content saved in stopped_content_to_save)
                stopped_content = st.session_state.pop("stopped_content_to_save", None)
                if stopped_content:
                    st.session_state["chat_messages"].append(
                        {"role": "assistant", "content": stopped_content}
                    )
                st.session_state["is_generating"] = False
                st.session_state["generation_started"] = False
                st.session_state["stop_generation"] = False
                st.rerun()
                return
        except Exception as exc:
            # Save error as a message in chat history so it persists
            error_content = f"⚠️ **Error:** {format_api_error(exc)}"
            st.session_state["chat_messages"].append({"role": "assistant", "content": error_content})
            st.session_state["is_generating"] = False
            st.session_state["generation_started"] = False
            st.session_state["stop_generation"] = False
            st.session_state.pop("current_assistant_partial", None)
            st.rerun()

    # Reset generating state
    st.session_state["is_generating"] = False
    st.session_state["generation_started"] = False
    st.session_state["stop_generation"] = False
    st.session_state.pop("current_assistant_partial", None)
    st.session_state.pop("pending_messages", None)  # Clean up saved messages

    # Only append full assistant message if not stopped
    if not st.session_state.get("stopped_content_to_save"):
        st.session_state["chat_messages"].append({"role": "assistant", "content": assistant_text})
    else:
        # Already appended above, no need to append again
        st.session_state.pop("stopped_content_to_save", None)
    # Rerun to refresh UI (re-enable input/clear stop button)
    st.rerun()
