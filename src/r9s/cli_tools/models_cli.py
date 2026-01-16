"""CLI handler for the `r9s models` command."""

from __future__ import annotations

import argparse
import json
from datetime import datetime
from typing import Any, TYPE_CHECKING, Iterable, Mapping, Sequence

import httpx
from httpx._types import PrimitiveData

from r9s import R9S
from r9s.cli_tools.config import get_api_key, resolve_base_url
from r9s.cli_tools.i18n import resolve_lang, t
from r9s.cli_tools.ui.terminal import error, header, info

if TYPE_CHECKING:
    pass


def _require_api_key(preset: str | None, lang: str) -> str:
    key = get_api_key(preset)
    if key:
        return key
    error(t("chat.api_key_required", lang))
    raise SystemExit(1)


def _dedupe_by_id(items: Iterable[Mapping[str, Any]]) -> list[Mapping[str, Any]]:
    by_id: dict[str, Mapping[str, Any]] = {}
    for item in items:
        model_id = str(item.get("id", "")).strip()
        if not model_id:
            continue
        if model_id not in by_id:
            by_id[model_id] = item
    return list(by_id.values())


def _fmt_list(value: Any) -> str | None:
    if not isinstance(value, list):
        return None
    items = [str(x) for x in value if x is not None and str(x).strip()]
    if not items:
        return None
    return ", ".join(items)


def _truncate(value: str, max_len: int) -> str:
    if max_len <= 0 or len(value) <= max_len:
        return value
    if max_len <= 1:
        return value[:max_len]
    return value[: max_len - 1] + "…"


def _request_models(
    *,
    api_key: str,
    base_url: str,
    expand: str | None,
    filters: Sequence[str] | None,
) -> Any:
    url = base_url.rstrip("/") + "/models"
    params: list[tuple[str, PrimitiveData]] = []
    if expand:
        params.append(("expand", expand))
    if filters:
        params.extend([("filter", f) for f in filters if f])
    query_params: httpx.QueryParams | None = None
    if params:
        query_params = httpx.QueryParams(params)

    try:
        with httpx.Client(timeout=10.0) as client:
            resp = client.get(
                url,
                headers={"Authorization": f"Bearer {api_key}", "Accept": "application/json"},
                params=query_params,
            )
    except httpx.HTTPError as exc:
        raise RuntimeError(f"请求失败: {exc}") from exc

    if resp.status_code != 200:
        raise RuntimeError(f"HTTP {resp.status_code}: {resp.text}")
    try:
        return resp.json()
    except ValueError as exc:
        raise RuntimeError("响应不是合法 JSON") from exc


def handle_models_list(args: argparse.Namespace) -> None:
    """List available models from the API."""
    lang = resolve_lang(getattr(args, "lang", None))
    api_key = _require_api_key(getattr(args, "api_key", None), lang)
    base_url = resolve_base_url(getattr(args, "base_url", None))
    expand = getattr(args, "expand", None)
    filters = getattr(args, "filter", None)
    show_details = bool(getattr(args, "details", False))
    verbose = bool(getattr(args, "verbose", False))

    try:
        if verbose or expand or filters:
            payload = _request_models(
                api_key=api_key, base_url=base_url, expand=expand, filters=filters
            )
        else:
            with R9S(api_key=api_key, server_url=base_url) as r9s:
                response = r9s.models.list()
            payload = response.model_dump(by_alias=True)
    except Exception as exc:
        error(f"Failed to fetch models: {exc}")
        raise SystemExit(1)

    if verbose:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return

    models: list[Any] = []
    if isinstance(payload, dict) and isinstance(payload.get("data"), list):
        models = payload["data"]
    elif isinstance(payload, list):
        models = payload

    if not models:
        info("No models available.")
        return

    if show_details:
        header(f"Available Models ({len(models)})")
        # Normalize to dict-like items
        model_dicts: list[Mapping[str, Any]] = []
        for item in models:
            if isinstance(item, Mapping):
                model_dicts.append(item)
            elif isinstance(item, str):
                model_dicts.append({"id": item})

        model_dicts = _dedupe_by_id(model_dicts)
        max_id_len = max(
            (len(str(m.get("id", ""))) for m in model_dicts),
            default=len("id"),
        )
        max_owner_len = max(
            (len(str(m.get("owned_by", ""))) for m in model_dicts),
            default=len("owned_by"),
        )
        max_id_len = max(max_id_len, len("id"))
        max_owner_len = max(max_owner_len, len("owned_by"))

        has_context_length = any(
            isinstance(m.get("context_length"), int) for m in model_dicts
        )
        has_modality = any(
            isinstance(m.get("modality"), str) and m["modality"] for m in model_dicts
        )
        has_channels = any(_fmt_list(m.get("channels")) for m in model_dicts)
        has_endpoints = any(_fmt_list(m.get("endpoints")) for m in model_dicts)

        max_context_len = len("context_length")
        if has_context_length:
            max_context_len = max(
                max_context_len,
                max(
                    (
                        len(str(m.get("context_length")))
                        for m in model_dicts
                        if isinstance(m.get("context_length"), int)
                    ),
                    default=max_context_len,
                ),
            )

        # Optional columns can get very wide; keep them readable.
        max_modality_len = min(
            40,
            max(
                len("modality"),
                max(
                    (
                        len(str(m.get("modality", "")))
                        for m in model_dicts
                        if isinstance(m.get("modality"), str) and m["modality"]
                    ),
                    default=len("modality"),
                ),
            ),
        )
        max_channels_len = min(
            40,
            max(
                len("channels"),
                max(
                    (
                        len(s)
                        for s in (_fmt_list(m.get("channels")) for m in model_dicts)
                        if s
                    ),
                    default=len("channels"),
                ),
            ),
        )
        # For endpoints column, allow --no-truncate to show full content
        no_truncate = bool(getattr(args, "no_trunc", False))
        if no_truncate:
            max_endpoints_len = max(
                len("endpoints"),
                max(
                    (
                        len(s)
                        for s in (_fmt_list(m.get("endpoints")) for m in model_dicts)
                        if s
                    ),
                    default=len("endpoints"),
                ),
            )
        else:
            max_endpoints_len = min(
                60,
                max(
                    len("endpoints"),
                    max(
                        (
                            len(s)
                            for s in (_fmt_list(m.get("endpoints")) for m in model_dicts)
                            if s
                        ),
                        default=len("endpoints"),
                    ),
                ),
            )

        header_cols: list[tuple[str, int]] = [
            ("id", max_id_len),
            ("owned_by", max_owner_len),
            ("created", len("created")),
        ]
        if has_context_length:
            header_cols.append(("context_length", max_context_len))
        if has_modality:
            header_cols.append(("modality", max_modality_len))
        if has_channels:
            header_cols.append(("channels", max_channels_len))
        if has_endpoints:
            header_cols.append(("endpoints", max_endpoints_len))

        header_line = "  " + "  ".join(f"{name:<{width}}" for name, width in header_cols)
        sep_line = "  " + "  ".join("-" * width for _, width in header_cols)
        print(header_line)
        print(sep_line)

        def _sort_key(m: Mapping[str, Any]) -> tuple[str, str]:
            return (str(m.get("owned_by", "")), str(m.get("id", "")))

        for m in sorted(model_dicts, key=_sort_key):
            model_id = str(m.get("id", ""))
            owned_by = str(m.get("owned_by", ""))
            created = m.get("created")
            created_str = "-"
            if isinstance(created, int):
                created_str = datetime.fromtimestamp(created).strftime("%Y-%m-%d")

            row_parts: list[str] = [
                f"{model_id:<{max_id_len}}",
                f"{owned_by:<{max_owner_len}}",
                f"{created_str:<{len('created')}}",
            ]

            if has_context_length:
                context_str = "-"
                if isinstance(m.get("context_length"), int):
                    context_str = str(m["context_length"])
                row_parts.append(f"{context_str:<{max_context_len}}")

            if has_modality:
                modality = "-"
                if isinstance(m.get("modality"), str) and m["modality"]:
                    modality = _truncate(str(m["modality"]), max_modality_len)
                row_parts.append(f"{modality:<{max_modality_len}}")

            if has_channels:
                channels_str = _fmt_list(m.get("channels")) or "-"
                channels_str = _truncate(channels_str, max_channels_len)
                row_parts.append(f"{channels_str:<{max_channels_len}}")

            if has_endpoints:
                endpoints_str = _fmt_list(m.get("endpoints")) or "-"
                endpoints_str = _truncate(endpoints_str, max_endpoints_len)
                row_parts.append(f"{endpoints_str:<{max_endpoints_len}}")

            print("  " + "  ".join(row_parts))
        return

    # ids: one model per line
    ids: list[str] = []
    for item in models:
        if isinstance(item, Mapping) and "id" in item:
            ids.append(str(item["id"]))
        elif isinstance(item, str):
            ids.append(item)

    for model_id in sorted(set(i for i in ids if i)):
        print(model_id)
