"""A card's page, the task that holds it, and its saved files."""

import re
from typing import TYPE_CHECKING

from lem.kernel.errors import Refusal

if TYPE_CHECKING:
    from datetime import datetime
    from pathlib import Path

PAGE_ID = re.compile(r"[A-Za-z0-9][A-Za-z0-9_-]{0,127}")


def checked(page: str) -> str:
    """The page's id, safe as one part of a file name."""
    if not PAGE_ID.fullmatch(page):
        raise Refusal(
            "ask-page", f"{page!r} is no page id", "use the id printed by lem ask"
        )
    return page


def question_id(page: str) -> str:
    """The key used by the task's question and the board's card views."""
    return f"card:{checked(page)}"


def copies(folder: Path, page: str) -> Path:
    """Where the card's files stay for the board and its waiter."""
    return folder / "cards" / checked(page)


def answer_at(folder: Path, at: datetime) -> Path:
    """The immutable answer artifact named by the time on the task's answer."""
    name = at.strftime("answer-%Y%m%dT%H%M%S%fZ.json")
    return folder / name
