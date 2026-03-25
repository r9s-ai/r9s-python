from __future__ import annotations

import json
from typing import Any, Dict, Iterator, Optional

from r9s import models, utils
from r9s.cli_tools.stream_timing import iter_sse_blocks, parse_sse_block
from r9s.conversation.models import (
    ConversationEvent,
    ConversationProtocol,
    ConversationRequest,
    ConversationResult,
)
from r9s.sdk import R9S


def resolve_protocol(request: ConversationRequest) -> ConversationProtocol:
    # Phase 1 keeps current behavior and defaults to chat completions.
    return request.protocol or "chat_completions"


def content_to_text(content: Any) -> str:
    if content is None:
        return ""
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts = []
        for item in content:
            if isinstance(item, dict):
                if item.get("type") == "text" and isinstance(item.get("text"), str):
                    parts.append(item["text"])
            else:
                item_type = getattr(item, "type", None)
                item_text = getattr(item, "text", None)
                if item_type == "text" and isinstance(item_text, str):
                    parts.append(item_text)
        if parts:
            return "".join(parts)
    try:
        return json.dumps(content, ensure_ascii=False)
    except Exception:
        return str(content)


def _build_chat_kwargs(
    request: ConversationRequest, *, stream: bool, http_headers: Optional[Dict[str, str]] = None
) -> Dict[str, Any]:
    return {
        "model": request.model,
        "messages": request.messages,
        "stream": stream,
        "temperature": request.temperature,
        "top_p": request.top_p,
        "max_tokens": request.max_tokens,
        "presence_penalty": request.presence_penalty,
        "frequency_penalty": request.frequency_penalty,
        "http_headers": http_headers if http_headers is not None else request.http_headers,
    }


def run_conversation(request: ConversationRequest) -> ConversationResult:
    protocol = resolve_protocol(request)
    if protocol != "chat_completions":
        raise ValueError(f"Unsupported conversation protocol: {protocol}")

    with R9S(api_key=request.api_key, server_url=request.base_url) as r9s:
        res = r9s.chat.create(**_build_chat_kwargs(request, stream=False))

    text = ""
    if res.choices and res.choices[0].message:
        text = content_to_text(res.choices[0].message.content)
    usage = res.usage
    return ConversationResult(
        text=text,
        request_id=getattr(res, "id", ""),
        input_tokens=usage.prompt_tokens if usage else 0,
        output_tokens=usage.completion_tokens if usage else 0,
        protocol=protocol,
        raw=res,
    )


def stream_conversation(request: ConversationRequest) -> Iterator[ConversationEvent]:
    protocol = resolve_protocol(request)
    if protocol != "chat_completions":
        raise ValueError(f"Unsupported conversation protocol: {protocol}")

    with R9S(api_key=request.api_key, server_url=request.base_url) as r9s:
        stream = r9s.chat.create(**_build_chat_kwargs(request, stream=True))
        response = getattr(stream, "response", None)
        if response is None:
            yield from _stream_via_sdk_events(stream, protocol)
            return
        try:
            yield from _stream_via_sse_response(response, protocol)
        finally:
            try:
                response.close()
            except Exception:
                pass


def _stream_via_sse_response(response: Any, protocol: ConversationProtocol) -> Iterator[ConversationEvent]:
    decoder = lambda raw: utils.unmarshal_json(  # noqa: E731
        raw, models.CreateChatCompletionResponseBody
    ).data

    request_id = ""
    input_tokens = 0
    output_tokens = 0

    for block in iter_sse_blocks(response):
        server_event, is_probe = parse_sse_block(block)
        if is_probe:
            yield ConversationEvent(type="probe", protocol=protocol)
            continue
        if server_event is None:
            continue

        data = server_event.get("data")
        if isinstance(data, str) and data == "[DONE]":
            yield ConversationEvent(
                type="done",
                request_id=request_id,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                protocol=protocol,
            )
            break
        if isinstance(data, dict) and "error" in data:
            raise RuntimeError(str(data["error"]))

        event = decoder(json.dumps(server_event))
        if not request_id and getattr(event, "id", None):
            request_id = event.id
        if getattr(event, "usage", None):
            usage = event.usage
            if usage:
                input_tokens = usage.prompt_tokens
                output_tokens = usage.completion_tokens
        if not event.choices:
            continue
        delta = event.choices[0].delta
        piece = getattr(delta, "content", None) or ""
        if not piece:
            continue
        if not isinstance(piece, str):
            piece = content_to_text(piece)
        yield ConversationEvent(
            type="text_delta",
            text=piece,
            request_id=request_id,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            protocol=protocol,
            raw=event,
        )
    else:
        yield ConversationEvent(
            type="done",
            request_id=request_id,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            protocol=protocol,
        )


def _stream_via_sdk_events(stream: Any, protocol: ConversationProtocol) -> Iterator[ConversationEvent]:
    request_id = ""
    input_tokens = 0
    output_tokens = 0

    for event in stream:
        if not request_id and getattr(event, "id", None):
            request_id = event.id
        usage = getattr(event, "usage", None)
        if usage:
            input_tokens = getattr(usage, "prompt_tokens", 0) or input_tokens
            output_tokens = getattr(usage, "completion_tokens", 0) or output_tokens
        choices = getattr(event, "choices", None)
        if not choices:
            continue
        delta = choices[0].delta
        piece = getattr(delta, "content", None) or ""
        if not piece:
            continue
        if not isinstance(piece, str):
            piece = content_to_text(piece)
        yield ConversationEvent(
            type="text_delta",
            text=piece,
            request_id=request_id,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            protocol=protocol,
            raw=event,
        )

    yield ConversationEvent(
        type="done",
        request_id=request_id,
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        protocol=protocol,
    )
