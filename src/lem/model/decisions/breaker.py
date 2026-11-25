"""The circuit breaker: it stops one task, for two causes and no others
(`decisions.cmd_breaker` on `main`).

The next step cannot be reversed by a later "no" (`irreversible`: it destroys or rewrites data
outside the worktree, writes to a system outside the repository beyond what the settings allow,
sends something to a person, or spends money; the lead says which, no code can tell), or no
option of the ladder keeps the outcome the owner approved (`criteria`). The record keeps the
breaker's document under its number, and the breaker holds the task until his help, park or
drop. One breaker holds a task at a time, and none stops a landing.
"""

from types import MappingProxyType
from typing import TYPE_CHECKING, Literal

from msgspec.structs import replace

from lem.kernel.errors import Refusal
from lem.model.decisions import book
from lem.records.holds import BreakerHold
from lem.records.journal.task import StateNoted

if TYPE_CHECKING:
    from datetime import datetime

    from lem.records.decisions import Breaker
    from lem.records.record import Record
    from lem.records.task import Task

type Cause = Literal["irreversible", "criteria"]
type Kind = Literal["data", "system", "person", "money"]

CAUSES = MappingProxyType(
    {
        "irreversible": "the next step cannot be reversed by a later no",
        "criteria": "no option of the ladder keeps the outcome the owner approved",
    }
)
KINDS = MappingProxyType(
    {
        "data": "it destroys or rewrites data outside the worktree",
        "system": "it writes to a system outside the repository, beyond what the settings "
        "allow",
        "person": "it sends something to a person",
        "money": "it spends money",
    }
)
HANDOFF = "handoff.md"
LANDING = frozenset(("landing", "open"))


def kept_name(number: int) -> str:
    """The name the record keeps breaker `number`'s document under, beside `breaker.md`, so a
    later breaker of the task never writes over it."""
    return f"breaker-{number}.md"


def why_of(cause: Cause, kind: Kind | None) -> str:
    """The cause in words, with the kind of an irreversible step; a kind without that cause,
    and that cause without a kind, are refused."""
    if (cause == "irreversible") != (kind is not None):
        raise Refusal(
            "breaker-cause",
            "--irreversible goes with --cause irreversible, and only with it",
            "--cause irreversible --irreversible data|system|person|money, or --cause "
            "criteria alone",
        )
    said = CAUSES[cause]
    return f"{said} ({KINDS[kind]})" if kind else said


def trippable(task: Task) -> None:
    """Refuse a breaker for a task that ended, is with its landing, or waits on another."""
    book.writable(task)
    if task.status in LANDING:
        raise Refusal(
            "with-landing",
            f"{task.slug} is {task.status}: its build is done, and no breaker stops a landing",
            "a step of the landing that only the owner may take is his word, as "
            "stages/land.md says",
        )
    waiting = book.waiting(task)
    if waiting:
        raise Refusal(
            "breaker-waits",
            f"breaker {waiting[0].id} of {task.slug} waits for the owner already",
            "one breaker holds a task at a time, and its document says it",
        )


def tripped(record: Record, *, breaker: Breaker, why: str, now: datetime) -> Record:
    """The record with `breaker`, which holds the task with its line."""
    task = record.task
    trippable(task)
    if breaker.id != len(task.decisions) + 1:
        raise Refusal(
            "stale",
            f"{task.slug} took decision {breaker.id} meanwhile",
            "run lem decisions breaker again",
        )
    line = f"breaker {breaker.id} waits for the owner: {breaker.what}: {why}"
    noted = StateNoted(at=now, status=task.status, hold="breaker", line=line)
    held = replace(task, hold=BreakerHold(number=breaker.id, since=now))
    record = replace(record, task=held, journal=(*record.journal, noted))
    return book.added(record, breaker, now)
