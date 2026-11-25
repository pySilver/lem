"""The personas' read of the criteria: its start, what it found, and what a clear read lets the
lead freeze (`project.read_form` and `criteria.approve_held` on `main`).

The landing reads it before the pull request credits the read, so it has one form: the personas
asked and answered, each family that answered, each silent persona and why, the criteria read
and flagged, whether the families split, and the mark of the criteria read. A read in which
nobody answered is written down too, and started once more; after the second in a row the
criteria go on unread.
"""

import re
from typing import TYPE_CHECKING, Literal

from msgspec.structs import asdict, replace

from lem.kernel.errors import Refusal
from lem.model.criteria.digest import LENGTH
from lem.records.approvals import PersonaRead, Silent
from lem.records.base import Frozen

if TYPE_CHECKING:
    from datetime import datetime

    from lem.records.task import Task

# Who runs a read: Lem in the task's session, or the lead.
type By = Literal["lem", "lead"]
# Every project's cast has two people or more.
LEAST = 2
MARK = re.compile(f"[0-9a-f]{{{LENGTH}}}")
FORM = "criteria-read"
NOBODY = (
    "a read in which nobody answered names no family, flags nothing, does not split, and "
    "names each persona asked with --silent"
)


class Found(Frozen, frozen=True, kw_only=True):
    """What a read found: the personas asked and answered, the families that answered, the
    silent, the criteria read and flagged, a split, and the mark of the criteria read."""

    asked: int
    answered: int
    families: tuple[str, ...] = ()
    silent: tuple[Silent, ...] = ()
    criteria: int
    flagged: int
    split: bool = False
    digest: str


def silent_of(said: str) -> Silent:
    """A silent persona as typed, `PERSONA, FAMILY: WHY`."""
    name, colon, why = said.partition(":")
    named = "," in name and why.strip()
    if not colon or not named:
        raise Refusal(
            FORM,
            f"--silent {said!r} is not PERSONA, FAMILY: WHY",
            'name each silent persona as --silent "Ania, opus: the agent gave no answer"',
        )
    persona = " ".join(name.split())
    return Silent(name=persona, why=" ".join(why.split()))


def refused(found: Found) -> str | None:
    """Why `found` is no read's result, or None."""
    doubts = found.families or found.flagged or found.split
    unnamed = len(found.silent) < found.asked
    wrongs = (
        (found.asked < LEAST, "a read asks two personas at the least"),
        (found.answered > found.asked, "--answered is at most --asked"),
        (len(set(found.families)) < len(found.families), "each family is named once"),
        (bool(found.answered and not found.families), "a read names each family"),
        (
            not MARK.fullmatch(found.digest),
            "--digest is what lem criteria digest prints",
        ),
        (
            bool(not found.answered and (doubts or unnamed)),
            NOBODY,
        ),
    )
    return next((why for wrong, why in wrongs if wrong), None)


def ended(task: Task, by: By, now: datetime, found: Found | None) -> Task:
    """The task whose newest open read by `by` ended with `found`, or, with None, in silence:
    nobody answered. With no open read, the read starts and ends now."""
    fresh = PersonaRead(by=by, started=now)
    *before, newest = task.criteria.reads or (fresh,)
    if newest.ended is not None or newest.by != by:
        before = [*before, newest]
        newest = fresh
    shown = asdict(found) if found else {}
    done = replace(newest, ended=now, **shown)
    return replace(task, criteria=replace(task.criteria, reads=(*before, done)))


def started(task: Task, by: By, now: datetime) -> Task:
    """The task with a read that starts now."""
    read = PersonaRead(by=by, started=now)
    reads = (*task.criteria.reads, read)
    return replace(task, criteria=replace(task.criteria, reads=reads))


def clear(task: Task, digest: str) -> Refusal | None:
    """Why the lead may not freeze the criteria of mark `digest` on a read: no read of them, a
    first read nobody answered, or a doubt (a flag, a split), which waits for the owner."""
    reads = [read for read in task.criteria.reads if read.ended is not None]
    last = reads[-1] if reads else None
    if last is None or last.digest != digest:
        of = "there is none" if last is None else f"it read {last.digest}"
        return Refusal(
            "not-read",
            f"--read freezes the criteria the newest read read, and {of}, not {digest}",
            "run the persona read over these criteria first (stages/plan.md, step 1)",
        )
    before = reads[-2] if len(reads) > 1 else last
    if last.answered == 0 and (before is last or before.answered):
        return Refusal(
            "unanswered",
            "nobody answered the newest read of the criteria",
            "start it once more; after a second read in a row that nobody answered, the "
            "build goes on with the criteria as they are",
        )
    if last.flagged or last.split:
        return Refusal(
            "doubt",
            "the newest read flagged a criterion or split between the families",
            "the criteria wait for the owner: only his approval freezes them",
        )
    return None
