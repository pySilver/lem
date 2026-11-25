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


def script_of(root: Path) -> str:
    """Pele is part of the page so a file and an overlay need no network."""
    path = root / "skills" / "lem" / "assets" / "vendor" / "pele.js"
    script = path.read_text(encoding="utf-8")
    return f"<script>{script}</script>"
