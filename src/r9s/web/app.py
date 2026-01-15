from __future__ import annotations

import streamlit as st

from r9s.web.common import apply_custom_styles, render_config
from r9s.web.nav_pages import agents, audio, chat, image_generation


def main() -> None:
    st.set_page_config(
        page_title="r9s Web",
        page_icon="https://routetokens.com/logo/logo.svg",
        layout="wide",
    )
    apply_custom_styles()
    cfg = render_config()
    if cfg is None:
        st.stop()

    def page_chat() -> None:
        chat.run(cfg)

    def page_agents() -> None:
        agents.run(cfg)

    def page_images() -> None:
        image_generation.run(cfg)

    def page_audio() -> None:
        audio.run(cfg)

    chat_page = st.Page(
        page_chat, title="Chat", icon=":material/chat:", url_path="chat", default=True
    )
    agents_page = st.Page(page_agents, title="Agents", icon=":material/groups:", url_path="agents")
    images_page = st.Page(
        page_images,
        title="Image Generation",
        icon=":material/image:",
        url_path="images",
    )
    audio_page = st.Page(page_audio, title="Audio", icon=":material/graphic_eq:", url_path="audio")

    pg = st.navigation(
        {
            "Core": [chat_page, agents_page],
            "Media": [images_page, audio_page],
        }
    )
    pg.run()


if __name__ == "__main__":
    main()
