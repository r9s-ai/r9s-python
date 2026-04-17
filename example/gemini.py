"""
Gemini Native API Examples
Demonstrates various ways to use the R9S Gemini native API.

Note: This file uses dict literals for simplicity and readability.
Type hints are suppressed with # type: ignore comments where needed.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any
import base64
import os

from r9s import R9S


OUTPUT_DIR = Path("./gemini")


def _iter_parts(response: Any) -> list[dict[str, Any]]:
    if not response.candidates:
        return []

    parts: list[dict[str, Any]] = []
    for candidate in response.candidates:
        content = getattr(candidate, "content", None)
        if content and getattr(content, "parts", None):
            parts.extend(content.parts)
    return parts


def _save_inline_images(response: Any, prefix: str) -> list[Path]:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    saved_files: list[Path] = []
    image_index = 0
    for part in _iter_parts(response):
        inline_data = part.get("inlineData") or part.get("inline_data")
        if not isinstance(inline_data, dict):
            continue

        data = inline_data.get("data")
        mime_type = inline_data.get("mimeType") or inline_data.get("mime_type")
        if not isinstance(data, str):
            continue

        extension = "png"
        if isinstance(mime_type, str) and "/" in mime_type:
            extension = mime_type.split("/", 1)[1]

        image_index += 1
        output_path = OUTPUT_DIR / f"{prefix}_{image_index}.{extension}"
        output_path.write_bytes(base64.b64decode(data))
        saved_files.append(output_path)

    return saved_files


def generate_text() -> None:
    """Example 1: generateContent text output"""
    print("\n" + "=" * 60)
    print("Example 1: Gemini generateContent Text")
    print("=" * 60)

    with R9S(
        api_key=os.getenv("R9S_API_KEY", ""),
        server_url=os.getenv("R9S_BASE_URL"),
        timeout_ms=1000 * 60 * 10,
    ) as r9s:
        res = r9s.gemini.generate_content(
            model="gemini-3-flash-preview",
            contents=[
                {
                    "parts": [{"text": "What is quantum mechanics?"}],
                }
            ],
            generation_config={
                "maxOutputTokens": 1024,
            },
        )

    text_chunks = [
        part["text"] for part in _iter_parts(res) if isinstance(part.get("text"), str)
    ]
    if text_chunks:
        print(f"Assistant: {''.join(text_chunks)}")
    else:
        print("No text content found in response.")
    if res.usage_metadata:
        print(f"Usage: {res.usage_metadata}")


def generate_image() -> None:
    """Example 2: generateContent image output"""
    print("\n" + "=" * 60)
    print("Example 2: Gemini generateContent Image")
    print("=" * 60)

    with R9S(
        api_key=os.getenv("R9S_API_KEY", ""),
        server_url=os.getenv("R9S_BASE_URL"),
        timeout_ms=1000 * 60 * 10,
    ) as r9s:
        res = r9s.gemini.generate_content(
            model="gemini-2.5-flash-image",
            contents=[
                {
                    "parts": [
                        {
                            "text": "Create a picture of a nano banana dish in a fancy restaurant with a Gemini theme"
                        }
                    ],
                }
            ],
            generation_config={
                "responseModalities": ["IMAGE"],
                "imageConfig": {
                    "aspectRatio": "16:9",
                    "imageSize": "1K",
                },
            },
        )

    output_files = _save_inline_images(res, "generate_image")
    if output_files:
        for output_file in output_files:
            print(f"Saved image to: {output_file}")
    else:
        print("No inline image found in response.")


def stream_image() -> None:
    """Example 3: streamGenerateContent image output"""
    print("\n" + "=" * 60)
    print("Example 3: Gemini streamGenerateContent Image")
    print("=" * 60)

    latest_event = None
    with R9S(
        api_key=os.getenv("R9S_API_KEY", ""),
        server_url=os.getenv("R9S_BASE_URL"),
        timeout_ms=1000 * 60 * 10,
    ) as r9s:
        stream = r9s.gemini.stream_generate_content(
            model="gemini-2.5-flash-image",
            contents=[
                {
                    "parts": [
                        {
                            "text": "Create a picture of a nano banana dish in a fancy restaurant with a Gemini theme"
                        }
                    ],
                }
            ],
            generation_config={
                "responseModalities": ["IMAGE"],
                "imageConfig": {
                    "aspectRatio": "16:9",
                    "imageSize": "1K",
                },
            },
        )

        event_count = 0
        for event in stream:
            event_count += 1
            latest_event = event
            print(f"Received event #{event_count}")

    if latest_event is None:
        print("No stream event received.")
        return

    output_files = _save_inline_images(latest_event, "stream_image")
    if output_files:
        for output_file in output_files:
            print(f"Saved image to: {output_file}")
    else:
        print("No inline image found in final stream event.")


def stream_text() -> None:
    """Example 4: streamGenerateContent text output"""
    print("\n" + "=" * 60)
    print("Example 4: Gemini streamGenerateContent Text")
    print("=" * 60)

    with R9S(
        api_key=os.getenv("R9S_API_KEY", ""),
        server_url=os.getenv("R9S_BASE_URL"),
        timeout_ms=1000 * 60 * 10,
    ) as r9s:
        stream = r9s.gemini.stream_generate_content(
            model="gemini-3-flash-preview",
            contents=[
                {
                    "parts": [{"text": "What is quantum mechanics?"}],
                }
            ],
            generation_config={
                "maxOutputTokens": 1024,
            },
        )

        print("Assistant: ", end="", flush=True)
        for event in stream:
            for part in _iter_parts(event):
                text = part.get("text")
                if isinstance(text, str):
                    print(text, end="", flush=True)
        print()


if __name__ == "__main__":
    generate_text()
    generate_image()
    stream_image()
    stream_text()
