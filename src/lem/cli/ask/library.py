"""The bundled Pele drawing library, for a question that contains a chart."""

import re
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pathlib import Path

FENCE = re.compile(r"^[ ]{0,3}(?:`{3,}|~{3,})[ \t]*mermaid\b", re.MULTILINE)


def has_charts(node: object) -> bool:
    """Whether a block or a markdown fence asks for a drawing."""
    if isinstance(node, dict):
        return "mermaid" in node or any(map(has_charts, node.values()))
    if isinstance(node, list):
        return any(map(has_charts, node))
    return isinstance(node, str) and bool(FENCE.search(node))


def scripts_of(root: Path, spec: object) -> tuple[str, ...]:
    """The installed runtime and, for a chart, the bundled Pele library."""
    skills = root / "skills"
    runtime = skills / "lem-ask" / "runtime" / "ask.js"
    script = runtime.read_text(encoding="utf-8")
    if not has_charts(spec):
        return (script,)
    pele = skills / "lem" / "assets" / "vendor" / "pele.js"
    return pele.read_text(encoding="utf-8"), script
