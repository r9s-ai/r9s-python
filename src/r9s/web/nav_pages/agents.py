from __future__ import annotations

import streamlit as st

from r9s.agents.local_store import LocalAgentStore, load_agent, load_version, save_agent
from r9s.web.common import AppConfig


def run(_cfg: AppConfig) -> None:
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

