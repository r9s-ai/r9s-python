from __future__ import annotations

import pytest

from r9s.skills.exceptions import InvalidSkillError
from r9s.skills.parser import parse_skill_markdown


def test_parse_skill_markdown() -> None:
    content = """---
name: code-review
description: Review code
allowed-tools: git bash
metadata:
  author: r9s
---

# Code Review

Use this skill.
"""
    metadata, body = parse_skill_markdown(content)
    assert metadata.name == "code-review"
    assert metadata.description == "Review code"
    assert metadata.allowed_tools == ["git", "bash"]
    assert metadata.metadata == {"author": "r9s"}
    assert body.startswith("# Code Review")


def test_parse_missing_frontmatter() -> None:
    content = "# No frontmatter here"
    with pytest.raises(InvalidSkillError, match="Missing YAML frontmatter"):
        parse_skill_markdown(content)


def test_parse_unterminated_frontmatter() -> None:
    content = """---
name: broken
description: Never closed
"""
    with pytest.raises(InvalidSkillError, match="Unterminated YAML frontmatter"):
        parse_skill_markdown(content)


def test_parse_empty_file() -> None:
    with pytest.raises(InvalidSkillError, match="empty"):
        parse_skill_markdown("")
    with pytest.raises(InvalidSkillError, match="empty"):
        parse_skill_markdown("   \n\n   ")


def test_parse_invalid_yaml() -> None:
    content = """---
name: [unclosed
description: bad yaml
---

body
"""
    with pytest.raises(InvalidSkillError, match="Invalid YAML"):
        parse_skill_markdown(content)


def test_parse_missing_required_fields() -> None:
    # Missing name
    content = """---
description: Has description but no name
---

body
"""
    with pytest.raises(InvalidSkillError, match="name is required"):
        parse_skill_markdown(content)

    # Missing description
    content = """---
name: has-name
---

body
"""
    with pytest.raises(InvalidSkillError, match="description is required"):
        parse_skill_markdown(content)
