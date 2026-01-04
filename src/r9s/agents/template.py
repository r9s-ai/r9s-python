from __future__ import annotations

import re
from typing import Dict, List


_VAR_RE = re.compile(r"\{\{(\w+)\}\}")


def extract_variables(template: str) -> List[str]:
    seen = []
    for match in _VAR_RE.finditer(template or ""):
        name = match.group(1)
        if name not in seen:
            seen.append(name)
    return seen


def render(template: str, variables: Dict[str, str]) -> str:
    def repl(match: re.Match[str]) -> str:
        name = match.group(1)
        if name in variables:
            return str(variables[name])
        return match.group(0)

    return _VAR_RE.sub(repl, template or "")
