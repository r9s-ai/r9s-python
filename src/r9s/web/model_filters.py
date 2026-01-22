from __future__ import annotations

from typing import Any, Iterable, List


CHAT_COMPLETIONS_ENDPOINT = "/v1/chat/completions"


def _as_str(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return value
    return str(value)


def _extract_model_id(item: Any) -> str:
    if isinstance(item, str):
        return item.strip()
    if isinstance(item, dict):
        return _as_str(item.get("id")).strip()
    return ""


def _extract_endpoints(item: Any) -> list[str]:
    if not isinstance(item, dict):
        return []
    raw = item.get("endpoints")
    if not isinstance(raw, list):
        return []
    out: list[str] = []
    for e in raw:
        s = _as_str(e).strip()
        if s:
            out.append(s)
    return out


def supports_endpoint(item: Any, endpoint: str) -> bool:
    endpoint = endpoint.strip()
    if not endpoint:
        return False
    for e in _extract_endpoints(item):
        if endpoint == e or endpoint in e:
            return True
    return False


def filter_model_ids_by_endpoint(items: Iterable[Any], endpoint: str) -> List[str]:
    seen: set[str] = set()
    result: List[str] = []
    for item in items:
        model_id = _extract_model_id(item)
        if not model_id or model_id in seen:
            continue
        if supports_endpoint(item, endpoint):
            seen.add(model_id)
            result.append(model_id)
    return result

