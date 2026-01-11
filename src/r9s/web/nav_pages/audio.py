from __future__ import annotations

from typing import Any, Dict

import streamlit as st

from r9s.web.common import AppConfig, format_api_error, get_env_default, r9s_client


def _audio_mime_type(response_format: str) -> str:
    mapping = {
        "mp3": "audio/mpeg",
        "wav": "audio/wav",
        "aac": "audio/aac",
        "flac": "audio/flac",
        "opus": "audio/opus",
        "pcm": "audio/pcm",
    }
    return mapping.get(response_format, "audio/mpeg")


def _audio_filename(response_format: str) -> str:
    ext = (response_format or "mp3").strip().lower()
    if not ext:
        ext = "mp3"
    return f"speech.{ext}"


def _extract_text_from_audio_response(response: Any) -> str:
    if isinstance(response, str):
        return response
    if response is None:
        return ""
    if hasattr(response, "text"):
        try:
            text = getattr(response, "text")
            if isinstance(text, str):
                return text
        except Exception:
            pass
    if hasattr(response, "model_dump_json"):
        try:
            return response.model_dump_json(indent=2)
        except Exception:
            pass
    return str(response)


def run(cfg: AppConfig) -> None:
    st.header("Audio")

    tts_tab, transcribe_tab, translate_tab = st.tabs(["Text-to-Speech", "Transcribe", "Translate"])

    with tts_tab:
        st.subheader("Text-to-Speech")
        tts_model = st.text_input("TTS model", value=get_env_default("R9S_TTS_MODEL", "tts-1"))
        voice = st.selectbox("Voice", options=["alloy", "echo", "fable", "onyx", "nova", "shimmer"], index=0)
        response_format = st.selectbox("Format", options=["mp3", "opus", "aac", "flac", "wav", "pcm"], index=0)
        speed = st.slider("Speed", min_value=0.25, max_value=4.0, value=1.0, step=0.05)
        text = st.text_area("Text", height=180, placeholder="Enter text to convert to speech...")

        if st.button("Generate speech", type="primary", key="audio_tts_generate"):
            if not tts_model.strip():
                st.error("TTS model is required")
            elif not text.strip():
                st.error("Text is required")
            else:
                with st.spinner("Generating speech..."):
                    try:
                        with r9s_client(cfg) as r9s:
                            res = r9s.audio.speech(
                                model=tts_model.strip(),
                                input=text.strip(),
                                voice=voice,
                                response_format=response_format,
                                speed=float(speed),
                            )
                            audio_bytes = res.read()
                        st.session_state["tts_audio_bytes"] = audio_bytes
                        st.session_state["tts_audio_format"] = response_format
                    except Exception as exc:
                        st.error(format_api_error(exc))

        audio_bytes = st.session_state.get("tts_audio_bytes")
        fmt = st.session_state.get("tts_audio_format", "mp3")
        if isinstance(audio_bytes, (bytes, bytearray)) and audio_bytes:
            st.divider()
            st.subheader("Result")
            st.audio(audio_bytes, format=_audio_mime_type(str(fmt)))
            st.download_button(
                "Download audio",
                data=audio_bytes,
                file_name=_audio_filename(str(fmt)),
                mime=_audio_mime_type(str(fmt)),
            )
            st.caption(f"Size: {len(audio_bytes) / 1024:.1f} KB")

    with transcribe_tab:
        st.subheader("Transcribe (Speech-to-Text)")
        stt_model = st.text_input("STT model", value=get_env_default("R9S_STT_MODEL", "whisper-1"))
        language = st.text_input("Language (optional, ISO-639-1)", value="")
        prompt = st.text_area("Prompt (optional)", height=80, value="", key="audio_transcribe_prompt")
        response_format = st.selectbox("Response format", options=["json", "text", "srt", "verbose_json", "vtt"], index=0)
        upload = st.file_uploader(
            "Upload audio",
            type=["mp3", "wav", "m4a", "mp4", "webm", "ogg", "flac", "opus", "aac"],
            key="audio_transcribe_upload",
        )

        if st.button("Transcribe", type="primary", key="audio_transcribe_btn"):
            if upload is None:
                st.error("Please upload an audio file")
            elif not stt_model.strip():
                st.error("STT model is required")
            else:
                data = upload.getvalue()
                kwargs: Dict[str, Any] = {
                    "file": {
                        "file_name": upload.name,
                        "content": data,
                        "content_type": upload.type or "application/octet-stream",
                    },
                    "model": stt_model.strip(),
                    "response_format": response_format,
                }
                if language.strip():
                    kwargs["language"] = language.strip()
                if prompt.strip():
                    kwargs["prompt"] = prompt.strip()

                with st.spinner("Transcribing..."):
                    try:
                        with r9s_client(cfg) as r9s:
                            res = r9s.audio.transcribe(**kwargs)
                        st.session_state["transcribe_result_text"] = _extract_text_from_audio_response(res)
                        st.session_state["transcribe_result_format"] = response_format
                    except Exception as exc:
                        st.error(format_api_error(exc))

        text = st.session_state.get("transcribe_result_text")
        fmt = st.session_state.get("transcribe_result_format", "json")
        if isinstance(text, str) and text.strip():
            st.divider()
            st.subheader("Result")
            st.text_area("Output", value=text, height=220)
            ext = "txt" if fmt in ("text",) else str(fmt)
            st.download_button(
                "Download",
                data=text.encode("utf-8"),
                file_name=f"transcription.{ext}",
                mime="text/plain; charset=utf-8",
            )

    with translate_tab:
        st.subheader("Translate (to English)")
        stt_model = st.text_input("STT model (translate)", value=get_env_default("R9S_STT_MODEL", "whisper-1"))
        prompt = st.text_area("Prompt (optional)", height=80, value="", key="audio_translate_prompt")
        response_format = st.selectbox(
            "Response format (translate)",
            options=["json", "text", "srt", "verbose_json", "vtt"],
            index=0,
        )
        upload = st.file_uploader(
            "Upload audio",
            type=["mp3", "wav", "m4a", "mp4", "webm", "ogg", "flac", "opus", "aac"],
            key="audio_translate_upload",
        )

        if st.button("Translate", type="primary", key="audio_translate_btn"):
            if upload is None:
                st.error("Please upload an audio file")
            elif not stt_model.strip():
                st.error("STT model is required")
            else:
                data = upload.getvalue()
                kwargs = {
                    "file": {
                        "file_name": upload.name,
                        "content": data,
                        "content_type": upload.type or "application/octet-stream",
                    },
                    "model": stt_model.strip(),
                    "response_format": response_format,
                }
                if prompt.strip():
                    kwargs["prompt"] = prompt.strip()

                with st.spinner("Translating..."):
                    try:
                        with r9s_client(cfg) as r9s:
                            res = r9s.audio.translate(**kwargs)
                        st.session_state["translate_result_text"] = _extract_text_from_audio_response(res)
                        st.session_state["translate_result_format"] = response_format
                    except Exception as exc:
                        st.error(format_api_error(exc))

        text = st.session_state.get("translate_result_text")
        fmt = st.session_state.get("translate_result_format", "json")
        if isinstance(text, str) and text.strip():
            st.divider()
            st.subheader("Result")
            st.text_area("Output", value=text, height=220)
            ext = "txt" if fmt in ("text",) else str(fmt)
            st.download_button(
                "Download",
                data=text.encode("utf-8"),
                file_name=f"translation.{ext}",
                mime="text/plain; charset=utf-8",
            )
