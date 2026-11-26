"""The Stop hook's reads of a pending question and its last mark."""

import json
import re
from pathlib import Path
from typing import NamedTuple

from lem.hooks import raw

PAGE_ID = re.compile(r"[A-Za-z0-9][A-Za-z0-9_-]{0,127}")
ASKING = ("blocked",)


class Overlay(NamedTuple):
    """One question in the current session, and the session's mark."""

    id: str
    path: str
    status: str | None


def pages(temporary: str) -> Path:
    """The resolved overlay folder, as the question command writes it."""
    return Path(temporary).resolve() / "lem-ask"


def shown(node: dict, folder: Path) -> Overlay | None:
    """Find an overlay of lem ask in this session's tree."""
    for overlay in node.get("htmlOverlays") or ():
        path = raw.text(overlay, "file")
        page = raw.text(overlay, "id")
        if not path or not PAGE_ID.fullmatch(page):
            continue
        if Path(path).resolve().parent == folder:
            return Overlay(page, path, node.get("status"))
    return None


def asking(folder: Path, page: Overlay) -> tuple[str, ...]:
    """The last wait's choice, or the choice of the open before any wait."""
    try:
        word = (folder / f"{page.id}.wait.html").read_bytes()
    except FileNotFoundError:
        return () if page.path.endswith(".no-status.html") else ASKING
    if word == b"status":
        return ASKING
    if word == b"no-status":
        return ()
    words = json.loads(word)
    return (
        tuple(words)
        if isinstance(words, list)
        and all(isinstance(one, str) and one for one in words)
        else ()
    )


def ended(task: str | None, page: str) -> bool:
    """Read a card's answer when the board took it before the overlay closed."""
    if task is None:
        return False
    try:
        record = json.loads((Path(task) / "task.json").read_bytes())
    except FileNotFoundError:
        return False
    key = f"card:{page}"
    return any(
        one.get("id") == key and one.get("answer") is not None
        for one in record["task"].get("questions", ())
    )
