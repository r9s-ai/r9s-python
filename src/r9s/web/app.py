from __future__ import annotations

import base64
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

import streamlit as st

from r9s.sdk import R9S
from r9s.agents.local_store import LocalAgentStore, load_agent, load_version, save_agent
from r9s.agents.template import render as render_agent_template
from r9s.skills.loader import format_skills_context, load_skills


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
        st.title("r9s Web")
        st.caption("使用 Streamlit 的最小 Web UI（Agents / 对话 / 图片）")
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
            st.warning("请先在侧边栏填写 R9S_API_KEY（或设置环境变量）。")
            return None
        if not base_url.strip():
            st.warning("请先填写 R9S_BASE_URL（或设置环境变量）。")
            return None
        if not model.strip():
            st.warning("请先填写 R9S_MODEL（或设置环境变量）。")
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
        st.subheader("新建 Agent")
        new_name = st.text_input("name", key="agent_new_name")
        new_model = st.text_input("model", key="agent_new_model")
        new_provider = st.text_input("provider", value="r9s", key="agent_new_provider")
        new_desc = st.text_input("description", key="agent_new_desc")
        new_instructions = st.text_area("instructions", height=220, key="agent_new_inst")
        new_skills_raw = st.text_input("skills（逗号分隔，可选）", key="agent_new_skills")
        if st.button("创建", type="primary", key="agent_create_btn"):
            if not new_name.strip():
                st.error("name 不能为空")
            elif not new_model.strip():
                st.error("model 不能为空")
            elif not new_instructions.strip():
                st.error("instructions 不能为空")
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
                st.success(f"已创建：{created.name}（version {created.current_version}）")
                st.rerun()

    with c2:
        st.subheader("管理已有 Agent")
        if not names:
            st.info("当前没有本地 agents（默认目录：~/.r9s/agents）。")
            return

        selected = st.selectbox("选择 Agent", options=names, key="agent_selected")
        agent = load_agent(selected)
        version = load_version(selected, agent.current_version)

        st.markdown(f"- current_version: `{agent.current_version}`")
        st.markdown(f"- model: `{version.model}`")
        st.markdown(f"- provider: `{version.provider}`")

        st.divider()
        inst = st.text_area("instructions（编辑后保存会产生新版本）", value=version.instructions, height=260)
        bump = st.checkbox("bump version（默认 true）", value=True)
        change_reason = st.text_input("change_reason（可选）", value="updated via web")

        skills_text = ", ".join(version.skills or [])
        skills_raw = st.text_input("skills（逗号分隔，可选）", value=skills_text)

        c2a, c2b = st.columns(2)
        with c2a:
            if st.button("保存更新", type="primary"):
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
                st.success("已更新")
                st.rerun()
        with c2b:
            if st.button("删除 Agent", type="secondary"):
                from r9s.agents.local_store import delete_agent

                delete_agent(selected)
                st.success("已删除")
                st.rerun()

        st.divider()
        st.subheader("回滚版本")
        versions = store.list_versions(selected)
        version_ids = [v.version for v in versions]
        rollback_to = st.selectbox("目标版本", options=version_ids, index=0)
        if st.button("设为 current_version"):
            agent.current_version = rollback_to
            save_agent(agent)
            st.success(f"已回滚到 {rollback_to}")
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
    st.header("对话")
    _init_chat_state()

    with st.sidebar:
        st.subheader("对话设置")
        use_stream = st.checkbox("流式输出", value=True)
        agent_names = [a.name for a in LocalAgentStore().list()]
        agent_name = st.selectbox("使用 Agent（可选）", options=["(none)"] + agent_names)
        vars_raw = st.text_area("Agent variables（JSON，可选）", value="{}", height=100)

    system_prompt: Optional[str] = None
    if agent_name != "(none)":
        try:
            import json

            variables_obj = json.loads(vars_raw or "{}")
            if not isinstance(variables_obj, dict):
                raise ValueError("variables 必须是 JSON object")
            variables = {str(k): str(v) for k, v in variables_obj.items()}
            system_prompt, _skills = _build_system_prompt_from_agent(agent_name, variables)
        except Exception as exc:
            st.sidebar.error(f"Agent variables 解析失败：{exc}")
            return

    for msg in st.session_state["chat_messages"]:
        role = msg.get("role", "assistant")
        content = msg.get("content")
        with st.chat_message(role):
            st.markdown(_as_text(content))

    upload = st.file_uploader("可选：上传一张图片作为本轮输入", type=["png", "jpg", "jpeg", "webp", "gif"])
    prompt = st.chat_input("输入消息…")
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
            st.error(f"请求失败：{exc}")
            return

    st.session_state["chat_messages"].append({"role": "assistant", "content": assistant_text})

    c1, c2 = st.columns(2)
    with c1:
        if st.button("清空对话", type="secondary"):
            st.session_state["chat_messages"] = []
            st.rerun()
    with c2:
        if system_prompt and st.button("查看 system prompt"):
            st.code(system_prompt)


def _render_images_page(cfg: AppConfig) -> None:
    st.header("图片生成")

    prompt = st.text_area("Prompt", height=120)
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        n = st.number_input("n", min_value=1, max_value=10, value=1, step=1)
    with col2:
        size = st.selectbox("size", options=["256x256", "512x512", "1024x1024"], index=2)
    with col3:
        response_format = st.selectbox("response_format", options=["url", "b64_json"], index=0)
    with col4:
        image_model = st.text_input("model（可选）", value=_get_env_default("R9S_IMAGE_MODEL", ""))

    if st.button("生成", type="primary"):
        if not prompt.strip():
            st.error("Prompt 不能为空")
            return
        model: Optional[str] = image_model.strip() or None
        with st.spinner("生成中…"):
            try:
                with _r9s_client(cfg) as r9s:
                    res = r9s.images.create(
                        prompt=prompt.strip(),
                        model=model,
                        n=int(n),
                        size=size,
                        response_format=response_format,
                    )
            except Exception as exc:
                st.error(f"请求失败：{exc}")
                return

        for i, img in enumerate(res.data):
            st.subheader(f"结果 {i + 1}")
            url = getattr(img, "url", None)
            b64_json = getattr(img, "b64_json", None)
            if url:
                st.image(url)
                st.code(url)
            elif b64_json:
                data = base64.b64decode(b64_json)
                st.image(data)
            revised = getattr(img, "revised_prompt", None)
            if revised:
                st.caption(f"revised_prompt: {revised}")


def main() -> None:
    st.set_page_config(page_title="r9s Web", layout="wide")
    cfg = _render_config()
    if cfg is None:
        st.stop()

    with st.sidebar:
        page = st.radio("页面", options=["对话", "Agents", "图片生成"], index=0)

    if page == "对话":
        _render_chat_page(cfg)
        return
    if page == "Agents":
        _render_agents_page()
        return
    if page == "图片生成":
        _render_images_page(cfg)
        return


if __name__ == "__main__":
    main()
