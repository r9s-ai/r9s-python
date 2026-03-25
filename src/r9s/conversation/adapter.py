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

CHAT_COMPLETIONS_ENDPOINT = "/v1/chat/completions"
ANTHROPIC_MESSAGES_ENDPOINT = "/v1/messages"
GEMINI_GENERATE_CONTENT_SUFFIX = ":generateContent"
GEMINI_STREAM_GENERATE_CONTENT_SUFFIX = ":streamGenerateContent"
DEFAULT_ANTHROPIC_MAX_TOKENS = 4096


def resolve_conversation_protocol(request: ConversationRequest) -> ConversationProtocol:
    if request.protocol is not None:
        return request.protocol
    if request.model_endpoints:
        return _infer_protocol_from_endpoints(request.model_endpoints)
    return _infer_protocol_from_model_name(request.model)


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


def run_conversation(request: ConversationRequest) -> ConversationResult:
    protocol = resolve_conversation_protocol(request)
    with R9S(api_key=request.api_key, server_url=request.base_url) as r9s:
        if protocol == "chat_completions":
            return _run_chat_completions_request(r9s, request, protocol)
        if protocol == "anthropic_messages":
            return _run_anthropic_messages_request(r9s, request, protocol)
        if protocol == "gemini_generate_content":
            return _run_gemini_generate_content_request(r9s, request, protocol)
    raise ValueError(f"Unsupported conversation protocol: {protocol}")


def stream_conversation(request: ConversationRequest) -> Iterator[ConversationEvent]:
    protocol = resolve_conversation_protocol(request)
    with R9S(api_key=request.api_key, server_url=request.base_url) as r9s:
        if protocol == "chat_completions":
            yield from _stream_chat_completions_request(r9s, request, protocol)
            return
        if protocol == "anthropic_messages":
            yield from _stream_anthropic_messages_request(r9s, request, protocol)
            return
        if protocol == "gemini_generate_content":
            yield from _stream_gemini_generate_content_request(r9s, request, protocol)
            return
    raise ValueError(f"Unsupported conversation protocol: {protocol}")


def will_apply_default_anthropic_max_tokens(request: ConversationRequest) -> bool:
    return (
        resolve_conversation_protocol(request) == "anthropic_messages"
        and request.max_tokens is None
    )


def _infer_protocol_from_endpoints(endpoints: list[str]) -> ConversationProtocol:
    normalized = [endpoint.strip() for endpoint in endpoints if endpoint and endpoint.strip()]

    has_chat_completions = any(
        CHAT_COMPLETIONS_ENDPOINT in endpoint for endpoint in normalized
    )
    has_anthropic_messages = any(
        ANTHROPIC_MESSAGES_ENDPOINT in endpoint for endpoint in normalized
    )
    has_gemini_generate_content = any(
        GEMINI_GENERATE_CONTENT_SUFFIX in endpoint
        or GEMINI_STREAM_GENERATE_CONTENT_SUFFIX in endpoint
        for endpoint in normalized
    )

    if has_chat_completions:
        return "chat_completions"
    if has_anthropic_messages:
        return "anthropic_messages"
    if has_gemini_generate_content:
        return "gemini_generate_content"
    return "chat_completions"


def _infer_protocol_from_model_name(model: str) -> ConversationProtocol:
    model_lower = model.strip().lower()
    if model_lower.startswith("claude") or "anthropic" in model_lower:
        return "anthropic_messages"
    if "gemini" in model_lower:
        return "gemini_generate_content"
    return "chat_completions"


def _adapt_request_to_chat_completions_kwargs(
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


def _run_chat_completions_request(r9s: R9S, request: ConversationRequest, protocol: ConversationProtocol) -> ConversationResult:
    res = r9s.chat.create(**_adapt_request_to_chat_completions_kwargs(request, stream=False))
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


def _run_anthropic_messages_request(r9s: R9S, request: ConversationRequest, protocol: ConversationProtocol) -> ConversationResult:
    res = r9s.messages.create(**_adapt_request_to_anthropic_messages_kwargs(request, stream=False))
    usage = getattr(res, "usage", None)
    return ConversationResult(
        text=_convert_anthropic_content_to_text(getattr(res, "content", None)),
        request_id=getattr(res, "id", ""),
        input_tokens=getattr(usage, "input_tokens", 0) if usage else 0,
        output_tokens=getattr(usage, "output_tokens", 0) if usage else 0,
        protocol=protocol,
        raw=res,
    )


def _run_gemini_generate_content_request(r9s: R9S, request: ConversationRequest, protocol: ConversationProtocol) -> ConversationResult:
    res = r9s.gemini.generate_content(**_adapt_request_to_gemini_generate_content_kwargs(request))
    usage = getattr(res, "usage_metadata", None)
    return ConversationResult(
        text=_convert_gemini_response_to_text(res),
        request_id=getattr(res, "response_id", ""),
        input_tokens=getattr(usage, "prompt_token_count", 0) if usage else 0,
        output_tokens=getattr(usage, "candidates_token_count", 0) if usage else 0,
        protocol=protocol,
        raw=res,
    )


def _stream_chat_completions_request(
    r9s: R9S, request: ConversationRequest, protocol: ConversationProtocol
) -> Iterator[ConversationEvent]:
    stream = r9s.chat.create(**_adapt_request_to_chat_completions_kwargs(request, stream=True))
    response = getattr(stream, "response", None)
    if response is None:
        yield from _stream_chat_completions_via_sdk_events(stream, protocol)
        return
    try:
        yield from _stream_chat_completions_via_sse_response(response, protocol)
    finally:
        try:
            response.close()
        except Exception:
            pass


def _stream_anthropic_messages_request(
    r9s: R9S, request: ConversationRequest, protocol: ConversationProtocol
) -> Iterator[ConversationEvent]:
    stream = r9s.messages.create(**_adapt_request_to_anthropic_messages_kwargs(request, stream=True))
    request_id = ""
    input_tokens = 0
    output_tokens = 0

    for event in stream:
        event_type = _read_stream_event_type(event)
        if event_type == "message_start":
            message = getattr(event, "message", None)
            if message is not None:
                request_id = getattr(message, "id", "") or request_id
                usage = getattr(message, "usage", None)
                if usage is not None:
                    input_tokens = getattr(usage, "input_tokens", 0) or input_tokens
                    output_tokens = getattr(usage, "output_tokens", 0) or output_tokens
            continue
        if event_type == "message_delta":
            usage = getattr(event, "usage", None)
            if usage is not None:
                output_tokens = getattr(usage, "output_tokens", 0) or output_tokens
            continue
        if event_type == "content_block_delta":
            piece = _convert_anthropic_stream_event_to_text_delta(event)
            if not piece:
                continue
            yield ConversationEvent(
                type="text_delta",
                text=piece,
                request_id=request_id,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                protocol=protocol,
                raw=event,
            )
            continue
        if event_type == "message_stop":
            break

    yield ConversationEvent(
        type="done",
        request_id=request_id,
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        protocol=protocol,
    )


def _stream_gemini_generate_content_request(
    r9s: R9S, request: ConversationRequest, protocol: ConversationProtocol
) -> Iterator[ConversationEvent]:
    stream = r9s.gemini.stream_generate_content(**_adapt_request_to_gemini_generate_content_kwargs(request))
    request_id = ""
    input_tokens = 0
    output_tokens = 0

    for event in stream:
        request_id = getattr(event, "response_id", "") or request_id
        usage = getattr(event, "usage_metadata", None)
        if usage is not None:
            input_tokens = getattr(usage, "prompt_token_count", 0) or input_tokens
            output_tokens = getattr(usage, "candidates_token_count", 0) or output_tokens
        piece = _convert_gemini_response_to_text(event)
        if not piece:
            continue
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


def _stream_chat_completions_via_sse_response(
    response: Any, protocol: ConversationProtocol
) -> Iterator[ConversationEvent]:
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


def _stream_chat_completions_via_sdk_events(
    stream: Any, protocol: ConversationProtocol
) -> Iterator[ConversationEvent]:
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


def _adapt_request_to_anthropic_messages_kwargs(
    request: ConversationRequest, *, stream: bool
) -> Dict[str, Any]:
    system_prompt, messages_no_system = _extract_system_prompt_from_openai_messages(request.messages)
    max_tokens = request.max_tokens
    if max_tokens is None:
        max_tokens = DEFAULT_ANTHROPIC_MAX_TOKENS
    return {
        "model": request.model,
        "messages": _adapt_openai_messages_to_anthropic_messages(messages_no_system),
        "system": system_prompt,
        "stream": stream,
        "temperature": request.temperature,
        "top_p": request.top_p,
        "max_tokens": max_tokens,
        "http_headers": request.http_headers,
    }


def _adapt_request_to_gemini_generate_content_kwargs(request: ConversationRequest) -> Dict[str, Any]:
    system_prompt, messages_no_system = _extract_system_prompt_from_openai_messages(request.messages)
    kwargs: Dict[str, Any] = {
        "model": request.model,
        "contents": _adapt_openai_messages_to_gemini_contents(messages_no_system),
        "http_headers": request.http_headers,
    }
    generation_config = _adapt_request_to_gemini_generation_config(request)
    if generation_config:
        kwargs["generation_config"] = generation_config
    if system_prompt:
        kwargs["system_instruction"] = {"parts": [{"text": system_prompt}]}
    return kwargs


def _extract_system_prompt_from_openai_messages(
    messages: list[models.MessageTypedDict],
) -> tuple[Optional[str], list[models.MessageTypedDict]]:
    system_parts: list[str] = []
    out: list[models.MessageTypedDict] = []
    for message in messages:
        role = message.get("role")
        if role == "system":
            text = content_to_text(message.get("content"))
            if text:
                system_parts.append(text)
            continue
        out.append(message)
    system_prompt = "\n\n".join(part for part in system_parts if part) or None
    return system_prompt, out


def _adapt_openai_messages_to_anthropic_messages(messages_in: list[models.MessageTypedDict]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for message in messages_in:
        _ensure_no_tools(message, protocol="anthropic_messages")
        role = message.get("role")
        if role not in {"user", "assistant"}:
            raise ValueError(f"Anthropic adapter does not support message role: {role}")
        out.append(
            {
                "role": role,
                "content": _adapt_openai_content_to_anthropic_content(message.get("content")),
            }
        )
    return out


def _adapt_openai_content_to_anthropic_content(content: Any) -> Any:
    if isinstance(content, str):
        return content
    if content is None:
        return ""
    if not isinstance(content, list):
        return content_to_text(content)

    blocks: list[dict[str, Any]] = []
    for item in content:
        if not isinstance(item, dict):
            blocks.append({"type": "text", "text": content_to_text(item)})
            continue
        item_type = item.get("type")
        if item_type == "text":
            blocks.append({"type": "text", "text": str(item.get("text", ""))})
            continue
        if item_type == "image_url":
            blocks.append(_adapt_openai_image_block_to_anthropic_image_block(item))
            continue
        raise ValueError(f"Anthropic adapter does not support content block: {item_type}")
    return blocks


def _adapt_openai_image_block_to_anthropic_image_block(item: dict[str, Any]) -> dict[str, Any]:
    image_url = item.get("image_url")
    if not isinstance(image_url, dict):
        raise ValueError("Anthropic adapter expected image_url block payload")
    url = image_url.get("url")
    if not isinstance(url, str) or not url.strip():
        raise ValueError("Anthropic adapter expected image_url.url")
    mime_type, data = _parse_data_url(url)
    return {
        "type": "image",
        "source": {
            "type": "base64",
            "media_type": mime_type,
            "data": data,
        },
    }


def _adapt_openai_messages_to_gemini_contents(messages_in: list[models.MessageTypedDict]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for message in messages_in:
        _ensure_no_tools(message, protocol="gemini_generate_content")
        role = message.get("role")
        if role not in {"user", "assistant"}:
            raise ValueError(f"Gemini adapter does not support message role: {role}")
        out.append(
            {
                "role": "user" if role == "user" else "model",
                "parts": _adapt_openai_content_to_gemini_parts(message.get("content")),
            }
        )
    return out


def _adapt_openai_content_to_gemini_parts(content: Any) -> list[dict[str, Any]]:
    if isinstance(content, str):
        return [{"text": content}]
    if content is None:
        return [{"text": ""}]
    if not isinstance(content, list):
        return [{"text": content_to_text(content)}]

    parts: list[dict[str, Any]] = []
    for item in content:
        if not isinstance(item, dict):
            parts.append({"text": content_to_text(item)})
            continue
        item_type = item.get("type")
        if item_type == "text":
            parts.append({"text": str(item.get("text", ""))})
            continue
        if item_type == "image_url":
            parts.append(_adapt_openai_image_block_to_gemini_inline_data(item))
            continue
        raise ValueError(f"Gemini adapter does not support content block: {item_type}")
    return parts


def _adapt_openai_image_block_to_gemini_inline_data(item: dict[str, Any]) -> dict[str, Any]:
    image_url = item.get("image_url")
    if not isinstance(image_url, dict):
        raise ValueError("Gemini adapter expected image_url block payload")
    url = image_url.get("url")
    if not isinstance(url, str) or not url.strip():
        raise ValueError("Gemini adapter expected image_url.url")
    mime_type, data = _parse_data_url(url)
    return {"inline_data": {"mime_type": mime_type, "data": data}}


def _adapt_request_to_gemini_generation_config(request: ConversationRequest) -> dict[str, Any]:
    config: dict[str, Any] = {}
    if request.temperature is not None:
        config["temperature"] = request.temperature
    if request.top_p is not None:
        config["topP"] = request.top_p
    if request.max_tokens is not None:
        config["maxOutputTokens"] = request.max_tokens
    if request.presence_penalty is not None:
        config["presencePenalty"] = request.presence_penalty
    if request.frequency_penalty is not None:
        config["frequencyPenalty"] = request.frequency_penalty
    return config


def _parse_data_url(url: str) -> tuple[str, str]:
    if not url.startswith("data:"):
        raise ValueError("Only data URL images are supported in phase 1 conversation adapters")
    header, _, data = url.partition(",")
    if not data:
        raise ValueError("Invalid data URL image payload")
    mime_type = header[5:].split(";", 1)[0].strip()
    if not mime_type:
        raise ValueError("Data URL image is missing mime type")
    return mime_type, data


def _ensure_no_tools(message: models.MessageTypedDict, *, protocol: str) -> None:
    role = message.get("role")
    if role == "tool":
        raise ValueError(f"{protocol} does not support tool messages in phase 1")
    if message.get("tool_calls"):
        raise ValueError(f"{protocol} does not support tool calls in phase 1")
    if message.get("tool_call_id"):
        raise ValueError(f"{protocol} does not support tool_call_id in phase 1")


def _convert_anthropic_content_to_text(content: Any) -> str:
    if not isinstance(content, list):
        return content_to_text(content)
    parts: list[str] = []
    for item in content:
        item_type = _read_item_attr(item, "type")
        if item_type == "text":
            text = _read_item_attr(item, "text")
            if isinstance(text, str):
                parts.append(text)
    return "".join(parts)


def _convert_anthropic_stream_event_to_text_delta(event: Any) -> str:
    delta = getattr(event, "delta", None)
    if delta is None:
        return ""
    if getattr(delta, "type", None) != "text_delta":
        return ""
    text = getattr(delta, "text", None)
    return text if isinstance(text, str) else ""


def _convert_gemini_response_to_text(res: Any) -> str:
    candidates = getattr(res, "candidates", None)
    if not candidates:
        return ""
    content = getattr(candidates[0], "content", None)
    if content is None:
        return ""
    return _convert_gemini_parts_to_text(getattr(content, "parts", None))


def _convert_gemini_parts_to_text(parts: Any) -> str:
    if not isinstance(parts, list):
        return ""
    out: list[str] = []
    for part in parts:
        if isinstance(part, dict):
            text = part.get("text")
        else:
            text = getattr(part, "text", None)
        if isinstance(text, str):
            out.append(text)
    return "".join(out)


def _read_stream_event_type(event: Any) -> str:
    if isinstance(event, dict):
        value = event.get("type")
        return value if isinstance(value, str) else ""
    value = getattr(event, "type", None)
    if isinstance(value, str):
        return value
    value = getattr(event, "TYPE", None)
    return value if isinstance(value, str) else ""


def _read_item_attr(item: Any, key: str) -> Any:
    if isinstance(item, dict):
        return item.get(key)
    return getattr(item, key, None)


# Backward-compatible aliases for callers during the rename.
resolve_protocol = resolve_conversation_protocol
will_use_default_anthropic_max_tokens = will_apply_default_anthropic_max_tokens
_build_anthropic_kwargs = _adapt_request_to_anthropic_messages_kwargs
_build_gemini_kwargs = _adapt_request_to_gemini_generate_content_kwargs
