"""A decision taken without the owner, or by him, as `lem decisions log` writes it
(`decisions.cmd_log` on `main`).

`--why` holds the gate's cite, `--said` what the personas answered; `--option` is each option the
decision had, `--vote` each persona's answer, one for each model family, and `--level` what each
level that ran answered. `owner` is a word of the owner's: his help on a breaker (`--breaker N`,
which settles it, with his own words in `--words`), a word nobody asked for, or his yes to skip
the personas' read; `lem` one that Lem took before the task had a lead.
"""

from typing import TYPE_CHECKING

from msgspec.structs import replace

from lem.kernel.errors import Refusal
from lem.model.decisions import book, ladder
from lem.model.decisions.words import spaced
from lem.records.base import Frozen
from lem.records.decisions import Level, Story, Taken
from lem.records.holds import BreakerHold, Parked

if TYPE_CHECKING:
    from datetime import datetime

    from lem.records.record import Record
    from lem.records.task import Task

VOTE = '"PERSONA, FAMILY=OPTION", one for each answer of a persona'
LEVEL = "NAME=ANSWER, one for each level that ran"


class Logged(Frozen, frozen=True, kw_only=True):
    """A decision as the command gives it, its chart read and checked, and the experts that
    answer on this machine for `--by experts`."""

    what: str
    chose: str
    why: str
    by: Level
    said: str | None = None
    undo: str | None = None
    options: tuple[str, ...] = ()
    votes: tuple[str, ...] = ()
    levels: tuple[str, ...] = ()
    unsettled: bool = False
    story: tuple[str | None, str | None, str | None] = (None, None, None)
    chart: str | None = None
    breaker: int | None = None
    words: str | None = None
    advisers: tuple[str, ...] = ()


def text(words: str | None, flag: str) -> str | None:
    """A text as kept, each run of spaces as one; an empty one is refused, never dropped."""
    if words is None:
        return None
    kept = spaced(words)
    if not kept:
        raise Refusal(
            ladder.CODE, f"{flag} is empty", f"give {flag} one plain sentence"
        )
    return kept


def checked(asked: Logged) -> None:
    """Refuse a decision whose level does not take what it says."""
    owners = asked.breaker is not None or asked.words is not None
    if asked.unsettled and asked.by != "lead":
        raise Refusal(
            ladder.CODE,
            "--unsettled is the lead's pick that no level settled",
            "it goes with --by lead",
        )
    if owners and asked.by != "owner":
        raise Refusal(
            ladder.CODE,
            "--breaker and --words are the owner's: his help on a breaker, in his words",
            "they go with --by owner",
        )
    votes = ladder.said_pairs(asked.votes, "--vote", VOTE)
    if asked.by == "personas":
        refusal = ladder.by_personas(votes, spaced(asked.chose))
        if refusal is not None:
            raise refusal


def story_of(asked: Logged) -> Story | None:
    """The story of the decision: required of an important one, all or none of any other."""
    if ladder.important(asked.by, unsettled=asked.unsettled) or any(asked.story):
        return ladder.story_of(*asked.story)
    return None


def taken_of(asked: Logged, number: int, now: datetime) -> Taken:
    """The decision as the record keeps it, number `number`."""
    checked(asked)
    return Taken(
        id=number,
        at=now,
        what=text(asked.what, "--what") or "",
        chose=text(asked.chose, "--chose") or "",
        why=text(asked.why, "--why") or "",
        by=asked.by,
        said=text(asked.said, "--said"),
        undo=text(asked.undo, "--undo"),
        options=tuple(text(one, "--option") or "" for one in asked.options),
        votes=ladder.said_pairs(asked.votes, "--vote", VOTE),
        levels=ladder.said_pairs(asked.levels, "--level", LEVEL),
        unsettled=asked.unsettled,
        chart=asked.chart,
        words=text(asked.words, "--words"),
        breaker=asked.breaker,
        advisers=asked.advisers,
        story=story_of(asked),
    )


def helpable(task: Task, number: int) -> None:
    """Refuse his help on a breaker that does not wait, or on a parked task."""
    waiting = {one.id for one in book.waiting(task)}
    if number not in waiting:
        raise Refusal(
            "no-breaker",
            f"breaker {number} of {task.slug} does not wait for his help",
            f"a later word of his is a decision of its own, with no --breaker; lem "
            f"decisions list {task.slug} names each breaker",
        )
    if isinstance(task.hold, Parked):
        raise Refusal(
            "parked",
            f"{task.slug} is parked",
            f"lem task resume {task.slug} brings its breaker back first, then his help "
            "settles it",
        )


def logged(record: Record, *, asked: Logged, now: datetime) -> Record:
    """The record with the decision `asked`; his help on the breaker that holds the task ends
    that hold."""
    task = record.task
    book.writable(task)
    if asked.breaker is not None:
        helpable(task, asked.breaker)
    taken = taken_of(asked, len(task.decisions) + 1, now)
    hold = task.hold
    if isinstance(hold, BreakerHold) and hold.number == asked.breaker:
        record = replace(record, task=replace(task, hold=None))
    return book.added(record, taken, now)
