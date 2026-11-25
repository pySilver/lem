"""The text of `talk.md`, and what `lem session talk` prints of it (`session.talk_text` on
`main`): a head that says where the copy runs from and what it left out, then each turn under
who said it and when."""

from typing import TYPE_CHECKING

import msgspec

from lem.app.sessions.talk_words import when, words_of
from lem.records.base import Frozen

if TYPE_CHECKING:
    from pathlib import Path

    from lem.adapters.claude_talk import Turn


type Turns = tuple[Turn, ...]
type Lefts = tuple[Left, ...]


class Left(Frozen, frozen=True, kw_only=True, omit_defaults=False):
    """An owner turn left out as another topic: when, its first words, and how many turns of
    the agent after it went with it."""

    at: str | None
    words: str
    lem_turns: int

    @classmethod
    def of(cls, turn: Turn, agents: int) -> Left:
        """The owner turn `turn` left out, with `agents` turns of the agent after it."""
        return cls(at=turn.at, words=words_of(turn.text), lem_turns=agents)


class Copied(Frozen, frozen=True, kw_only=True, omit_defaults=False):
    """The copy: the task, the file, how many turns of each, and what was left out."""

    task: str
    written: str = msgspec.field(name="file")
    turns: int
    owner_turns: int
    lem_turns: int
    left_out: tuple[Left, ...]

    @classmethod
    def of(cls, slug: str, path: Path, kept: Turns, left: Lefts) -> Copied:
        """The copy of `kept` into `path`."""
        owners = [turn for turn in kept if turn.who == "owner"]
        return cls(
            task=slug,
            written=str(path),
            turns=len(kept),
            owner_turns=len(owners),
            lem_turns=len(kept) - len(owners),
            left_out=left,
        )


def text_of(slug: str, kept: Turns, left: Lefts) -> str:
    """The whole text of `talk.md`."""
    head = head_of(slug, kept)
    blocks = (line for turn in kept for line in block_of(turn))
    return "\n".join((*head, *gaps_of(left), *blocks))


def head_of(slug: str, kept: tuple[Turn, ...]) -> tuple[str, ...]:
    """The title, and where the copy runs from."""
    first = kept[0]
    since = when(first.at)
    words = words_of(first.text)
    count = len(kept)
    line = (
        f"Copied word for word from the session where it was asked: {count} turns, from the "
        f'owner\'s turn of {since} that starts "{words}" to the newest turn.'
    )
    return (f"# The talk that led to the ask of {slug}", "", line, "")


def gaps_of(left: tuple[Left, ...]) -> tuple[str, ...]:
    """What was left out as another topic, a line each."""
    if not left:
        return ()
    lines = (gap_of(one) for one in left)
    return ("Left out as another topic:", "", *lines, "")


def gap_of(one: Left) -> str:
    """One owner turn left out, and the agent's turns with it."""
    since = when(one.at)
    return (
        f'- the owner\'s turn of {since} that starts "{one.words}", with {one.lem_turns} '
        "turns of the agent after it"
    )


def block_of(turn: Turn) -> tuple[str, ...]:
    """One turn under who said it and when."""
    who = "The owner" if turn.who == "owner" else "The agent"
    since = when(turn.at)
    return (f"## {who}, {since}", "", turn.text, "")
