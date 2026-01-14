from __future__ import annotations

from r9s.agents.template import extract_variables, render


def test_extract_variables_unique() -> None:
    template = "Hello {{name}} and {{name}} from {{company}}"
    assert extract_variables(template) == ["name", "company"]


def test_render_replaces_vars() -> None:
    assert render("Hi {{name}}", {"name": "Ada"}) == "Hi Ada"


def test_render_keeps_missing() -> None:
    assert render("Hi {{name}}", {}) == "Hi {{name}}"
