"""`lem session talk`: copy the turns of the session where the owner asked into the task's
`talk.md`, word for word (`session.cmd_talk` on `main`).

The copy runs from the newest owner turn that starts with the words `--from` gives to the newest
turn, each with who said it and only its text, less each owner turn that a `--leave` text
starts (another topic) with the agent's turns that answer it. The turns come from the harness's
reader of the session's transcript (`adapters/claude_talk_turns.py`).
"""

import itertools
from functools import partial
from operator import itemgetter
from typing import TYPE_CHECKING

from lem.app.sessions.talk_text import Copied, Left, text_of
from lem.app.sessions.talk_words import flat, lem_said, owner_turns, starts
from lem.kernel import files
from lem.kernel.errors import Refusal
from lem.store import guard

if TYPE_CHECKING:
    from pathlib import Path

    from lem.adapters.claude_talk import Turn
    from lem.app.sessions.here import Here

TALK = "talk.md"


type Asked = tuple[str, tuple[str, ...]]
type Found = tuple[tuple[Left, tuple[int, ...]], ...]


def copied(here: Here, slug: str, turns: tuple[Turn, ...], asked: Asked) -> Copied:
    """Write `talk.md` of the task from `turns`; `asked` is the `--from` words and the
    `--leave` words."""
    kept = from_start(turns, asked[0])
    found = tuple(map(partial(leaving, kept), asked[1]))
    shown = kept_shown(kept, found)
    left = tuple(map(itemgetter(0), found))
    text = text_of(slug, shown, left)
    return Copied.of(slug, written(here.folder(slug), text), shown, left)


def kept_shown(kept: tuple[Turn, ...], found: Found) -> tuple[Turn, ...]:
    """The turns of the copy less the ones left out."""
    out = {place for _, places in found for place in places}
    return tuple(turn for place, turn in enumerate(kept) if place not in out)


def from_start(turns: tuple[Turn, ...], start: str) -> tuple[Turn, ...]:
    """The turns from the newest owner turn that `start` starts; refused when none does."""
    if not flat(start):
        raise Refusal(
            "talk-from",
            "--from is empty",
            "give the first words of the owner's turn where the topic began",
        )
    places = [place for place, turn in enumerate(turns) if starts(turn, start)]
    if not places:
        raise Refusal(
            "talk-from",
            f"no turn of the owner starts with {start!r}",
            "give the first words of his turn where the topic began, as he typed them",
        )
    return turns[places[-1] :]


type Span = tuple[Left, tuple[int, ...]]


def leaving(kept: tuple[Turn, ...], words: str) -> Span:
    """The owner turn after the first that `words` starts, and the places it and the agent's
    turns right after it hold; refused when none does."""
    places = owner_turns(kept[1:], words)
    if not flat(words) or not places:
        raise Refusal(
            "talk-leave",
            f"no turn of the owner after the first one starts with {words!r}",
            "--leave names an owner turn of the copy, as he typed it",
        )
    first = places[-1] + 1
    span = (first, *answers(kept, first))
    return Left.of(kept[first], len(span) - 1), span


def answers(kept: tuple[Turn, ...], first: int) -> tuple[int, ...]:
    """The places of the agent's turns right after the owner turn at `first`."""
    after = kept[first + 1 :]
    agents = list(itertools.takewhile(lem_said, after))
    start = first + 1
    return tuple(range(start, start + len(agents)))


def written(folder: Path, text: str) -> Path:
    """Write `talk.md` whole in the task's folder."""
    guard.writable(folder.parents[1])
    path = folder / TALK
    files.write_whole(path, text.encode())
    return path
