"""The numbers of a task's progress card (`board_task.progress` on `main`): who works on it, its
last commit, how long it is open, its checks, its newest review, and its decisions."""

from typing import TYPE_CHECKING

from lem.board.inputs import clock
from lem.board.inputs.names import plural
from lem.board.inputs.task.now import Stat
from lem.board.views import rounds
from lem.board.views.panel.common import closed, stamp
from lem.board.views.panel.decided import decisions
from lem.board.views.panel.leads import lead_of

if TYPE_CHECKING:
    from lem.board.views.world import Seen, World
    from lem.records.landing.review import Reviewed
    from lem.records.record import Record

NONE = "–"
REPORT = "none: it ended with a report"


def stats(world: World, seen: Seen) -> tuple[Stat, ...]:
    """The six numbers of the task of `seen`."""
    record = seen.record
    worked = (who(record), commit(seen), open_for(world, record))
    return (*worked, checks(record), review(record), decisions(record))


def who(record: Record) -> Stat:
    """Who works on it: its lead, its investigator, or nobody yet."""
    lead = lead_of(record)
    task = record.task
    if lead is not None:
        shown, said = lead.tag, lead.stat
    elif task.investigation is not None:
        shown, said = (
            "investigator",
            "an investigator examined the bug or the question first",
        )
    else:
        shown = NONE
        said = "no agent was started" if closed(task) else "no agent was started yet"
    return Stat(label="Who works on it", shown=shown, said=said)


def commit(seen: Seen) -> Stat:
    """The newest commit of its branch."""
    head = seen.head
    if head is not None:
        return Stat(label="Last commit", shown=head.sha[:7], said=head.subject)
    task = seen.record.task
    said = (
        "no commit of its branch is on record"
        if closed(task)
        else "no commit on its branch yet"
    )
    return Stat(label="Last commit", shown=NONE, said=said)


def open_for(world: World, record: Record) -> Stat:
    """How long it is open, or was."""
    task = record.task
    said = f"opened {stamp(world, task.opened)}"
    if closed(task):
        length = clock.length((task.since - task.opened).total_seconds())
        return Stat(label="Open for", shown=length, said=said)
    when = clock.since(task.opened, world.clock.now)
    return Stat(label="Open for", shown=when.shown, when=when, said=said)


def checks(record: Record) -> Stat:
    """The last run of its checks: green or red, and how many commands."""
    checked = record.landing.checked if record.landing else None
    outcomes = checked.outcomes if checked else ()
    if not outcomes:
        answered = record.task.status == "answered"
        said = REPORT if answered else "they run before the pull request"
        return Stat(label="Checks", shown=NONE, said=said)
    red = any(not one.passed for one in outcomes)
    said = f"{plural(len(outcomes), 'command')} in the last run"
    if red:
        return Stat(label="Checks", shown="red", said=said, look="bad")
    return Stat(label="Checks", shown="green", said=said, look="ok")


def review(record: Record) -> Stat:
    """Its newest review: its verdict, its round and its kind."""
    reviews = record.landing.reviews if record.landing else ()
    if not reviews:
        answered = record.task.status == "answered"
        said = REPORT if answered else "after the checks, before the proposal"
        return Stat(label="Review", shown=NONE, said=said)
    newest = reviews[-1]
    verdict = rounds.verdict(newest)
    return Stat(
        label="Review",
        shown=verdict,
        said=round_of(newest),
        look="ok" if verdict == "clean" else "bad",
    )


def round_of(newest: Reviewed) -> str:
    """`round 2, a round with the profiles that fit`."""
    kind = rounds.KIND[newest.kind]
    return f"round {newest.attempt}, {kind}"
