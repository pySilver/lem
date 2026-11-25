"""One dated folder per question, hidden from git and kept by the state store."""

import re
from typing import TYPE_CHECKING

from lem.kernel.errors import Refusal
from lem.store import guard
from lem.store.places import STATE, checkout_of
from lem.store.retention.folders import EXPERT as NAME

if TYPE_CHECKING:
    from datetime import datetime
    from pathlib import Path

# The question's words in the folder name, as on main (2026-11-25).
TITLE_CHARS = 48
TITLE_WORDS = 6


def make(state: Path, question: str, at: datetime) -> Path:
    """Reserve a unique folder for a question before publishing its files."""
    top = state / "experts"
    top.mkdir(parents=True, exist_ok=True)
    found = re.findall(r"[a-z0-9]+", question.lower())
    words = "-".join(found[:TITLE_WORDS])
    title = words[:TITLE_CHARS].strip("-") or "question"
    stem = at.strftime("%Y-%m-%d-%H%M%S")
    return reserve(top / f"{stem}-{title}")


def reserve(first: Path) -> Path:
    """Reserve the name, with a number if another question used it."""
    folder = first
    number = 1
    while True:
        try:
            folder.mkdir()
        except FileExistsError:
            number += 1
            folder = first.with_name(f"{first.name}-{number}")
        else:
            return folder


def existing(start: Path, named: str) -> Path:
    """Read the saved question by its name, without following a path outside state."""
    state = checkout_of(start) / STATE
    guard.readable(state)
    top = state / "experts"
    folder = top / named
    if (
        NAME.fullmatch(named)
        and not folder.is_symlink()
        and (folder / "record.json").is_file()
    ):
        return folder
    raise Refusal(
        "expert-folder",
        f"the owner's expert folder {named!r} is invalid or absent",
        "use the folder name that lem experts brief printed",
    )
