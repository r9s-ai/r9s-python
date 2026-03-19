from __future__ import annotations

from r9s.web.model_filters import CHAT_COMPLETIONS_ENDPOINT, filter_model_ids_by_endpoint


def test_filter_model_ids_by_endpoint_keeps_order_and_dedupes() -> None:
    items = [
        {"id": "a", "endpoints": ["/v1/chat/completions"]},
        {"id": "b", "endpoints": ["/v1/images/generations"]},
        {"id": "a", "endpoints": ["/v1/chat/completions"]},  # dup
        {"id": "c", "endpoints": ["POST /v1/chat/completions"]},  # contains
        {"id": "d"},  # no endpoints
    ]
    assert filter_model_ids_by_endpoint(items, CHAT_COMPLETIONS_ENDPOINT) == ["a", "c"]


def test_filter_model_ids_by_endpoint_ignores_non_dict_items() -> None:
    items = ["x", 123, None, {"id": "y", "endpoints": ["/v1/chat/completions"]}]
    assert filter_model_ids_by_endpoint(items, CHAT_COMPLETIONS_ENDPOINT) == ["y"]

