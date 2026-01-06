"""CLI handler for the `r9s models` command."""

from __future__ import annotations

import argparse
from datetime import datetime
from typing import TYPE_CHECKING

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


def handle_models_list(args: argparse.Namespace) -> None:
    """List available models from the API."""
    lang = resolve_lang(getattr(args, "lang", None))
    api_key = _require_api_key(getattr(args, "api_key", None), lang)
    base_url = resolve_base_url(getattr(args, "base_url", None))

    try:
        with R9S(api_key=api_key, server_url=base_url) as r9s:
            response = r9s.models.list()
    except Exception as exc:
        error(f"Failed to fetch models: {exc}")
        raise SystemExit(1)

    models = response.data
    if not models:
        info("No models available.")
        return

    # Check output format
    show_details = getattr(args, "details", False)

    if show_details:
        header(f"Available Models ({len(models)})")
        # Find max lengths for alignment
        max_id_len = max(len(m.id) for m in models)
        max_owner_len = max(len(m.owned_by) for m in models)

        for m in sorted(models, key=lambda x: (x.owned_by, x.id)):
            created_str = datetime.fromtimestamp(m.created).strftime("%Y-%m-%d")
            print(
                f"  {m.id:<{max_id_len}}  {m.owned_by:<{max_owner_len}}  {created_str}"
            )
    else:
        # Simple list: just model names
        for m in sorted(models, key=lambda x: x.id):
            print(m.id)
