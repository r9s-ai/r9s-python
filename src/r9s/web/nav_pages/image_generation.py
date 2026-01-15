from __future__ import annotations

import base64
from typing import Any, Dict, Optional

import streamlit as st

from r9s.web.common import AppConfig, format_api_error, get_env_default, r9s_client


def run(cfg: AppConfig) -> None:
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
        image_model = st.text_input("model (optional)", value=get_env_default("R9S_IMAGE_MODEL", ""))

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
                with r9s_client(cfg) as r9s:
                    res = r9s.images.create(**kwargs)
            except Exception as exc:
                st.error(format_api_error(exc))
                return

        st.session_state["generated_images"] = []
        st.session_state["generated_urls"] = []
        for i, img in enumerate(res.data):
            url = getattr(img, "url", None)
            b64_json = getattr(img, "b64_json", None)
            image_data = None
            image_url = None

            if url:
                image_url = url
                try:
                    import urllib.request

                    with urllib.request.urlopen(url, timeout=30) as resp:
                        image_data = resp.read()
                except Exception:
                    pass
            elif b64_json:
                image_data = base64.b64decode(b64_json)

            revised = getattr(img, "revised_prompt", None)
            st.session_state["generated_images"].append(
                {
                    "index": i,
                    "data": image_data,
                    "url": image_url,
                    "model": model,
                    "revised_prompt": revised,
                }
            )

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
                        with r9s_client(cfg) as r9s:
                            edit_res = r9s.images.edit(**edit_kwargs)
                    except Exception as exc:
                        st.error(format_api_error(exc))
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

                    if edited_data:
                        st.session_state["generated_images"][edit_idx] = {
                            "index": edit_idx,
                            "data": edited_data,
                            "model": selected_img.get("model"),
                        }

