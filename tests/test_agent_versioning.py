from __future__ import annotations

import pytest

from r9s.agents.exceptions import InvalidVersionError
from r9s.agents.versioning import compare_versions, increment_version, parse_version


def test_parse_version() -> None:
    assert parse_version("1.2.3") == (1, 2, 3)


def test_increment_version() -> None:
    assert increment_version("1.2.3", bump="patch") == "1.2.4"
    assert increment_version("1.2.3", bump="minor") == "1.3.0"
    assert increment_version("1.2.3", bump="major") == "2.0.0"


def test_compare_versions() -> None:
    assert compare_versions("1.2.3", "1.2.3") == 0
    assert compare_versions("1.2.3", "1.2.4") == -1
    assert compare_versions("2.0.0", "1.9.9") == 1


def test_invalid_version() -> None:
    with pytest.raises(InvalidVersionError):
        parse_version("1.2")
