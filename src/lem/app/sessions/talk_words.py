"""The words of a turn as `lem session talk` matches, names and dates them."""

from functools import partial
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from lem.adapters.claude_talk import Turn

# How many words of a turn name it.
FIRST_WORDS = 8
# A moment's text to its minute: `2026-11-19T14:17`.
MINUTE = 16


def flat(text: str) -> str:
    """The words of `text` with one space between each."""
    return " ".join(text.split())


def starts(turn: Turn, words: str) -> bool:
    """Whether an owner turn starts with `words`, or its slash command's arguments do."""
    wanted = flat(words)
    said = (flat(turn.text), flat(turn.args or ""))
    owner = turn.who == "owner"
    return owner and any(one.startswith(wanted) for one in said)


def words_of(text: str) -> str:
    """The first words of a turn, with an ellipsis when it has more."""
    words = flat(text).split(" ")
    shown = " ".join(words[:FIRST_WORDS])
    return f"{shown} …" if len(words) > FIRST_WORDS else shown


def when(stamp: str | None) -> str:
    """`2026-11-19T14:17:34.495Z` as `2026-11-19 14:17 UTC`."""
    if not stamp or len(stamp) < MINUTE:
        return "an unknown time"
    minute = stamp[:MINUTE].replace("T", " ")
    return f"{minute} UTC"


def owner_turns(turns: tuple[Turn, ...], words: str) -> list[int]:
    """The places of the owner turns that `words` starts."""
    found = partial(starts, words=words)
    return [place for place, turn in enumerate(turns) if found(turn)]


def lem_said(turn: Turn) -> bool:
    """Whether the agent said the turn."""
    return turn.who == "lem"
