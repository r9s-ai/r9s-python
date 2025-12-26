from __future__ import annotations

import base64

from r9s.cli_tools.chat_cli import _build_user_message_from_piped_stdin
from r9s.cli_tools.chat_extensions import ChatContext


def test_build_user_message_from_piped_stdin_png() -> None:
    # Minimal bytes with a valid PNG signature (parser only checks header).
    png_bytes = b"\x89PNG\r\n\x1a\n" + b"\x00" * 8
    raw = b"\n" + png_bytes + b"\n"

    ctx = ChatContext(base_url="", model="")
    msg = _build_user_message_from_piped_stdin(raw, lang="en", exts=[], ctx=ctx)
    assert msg is not None
    assert msg.get("role") == "user"
    content = msg.get("content")
    assert isinstance(content, list)

    first = content[0]
    assert isinstance(first, dict)
    assert first.get("type") == "text"
    assert first.get("text") == "Describe this image."

    second = content[1]
    assert isinstance(second, dict)
    assert second.get("type") == "image_url"
    image_url = second.get("image_url")
    assert isinstance(image_url, dict)
    url = image_url.get("url")
    assert isinstance(url, str)
    assert url.startswith("data:image/png;base64,")
    assert url == "data:image/png;base64," + base64.b64encode(png_bytes).decode("ascii")
