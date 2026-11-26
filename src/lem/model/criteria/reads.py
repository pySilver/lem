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
DIGEST = "--digest is what lem criteria digest prints"
UNNAMED = "--silent names each distinct source that did not answer"
SOURCES = "--silent must cover each persona that gave no answer, within --asked"
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


def counted(found: Found) -> str | None:
    """Why the counts of `found` do not add up, or None (`project.read_form` on `main`)."""
    named = [family for family in found.families if family.strip()]
    wrongs = (
        (found.asked < LEAST, "a read asks two personas at the least"),
        (found.answered > found.asked, "--answered is at most --asked"),
        (len(set(named)) < len(found.families), "each family is named once, in words"),
        (bool(found.answered and not named), "a read names each family that answered"),
        (found.criteria < 1, "a read reads one criterion at the least"),
        (found.flagged > found.criteria, "no more criteria flagged than read"),
        (found.split and len(named) < LEAST, "a split is between two families"),
    )
    return next((why for wrong, why in wrongs if wrong), None)


def refused(found: Found) -> str | None:
    """Why `found` is no read's result, or None."""
    said = counted(found)
    if said is not None or not MARK.fullmatch(found.digest):
        return said or DIGEST
    doubts = found.families or found.flagged or found.split
    if not found.answered and doubts:
        return NOBODY
    return silent_refusal(found)


def silent_refusal(found: Found) -> str | None:
    """Each silent source is one seat, and a persona may have more than one seat."""
    sources = {
        tuple(part.strip() for part in entry.name.rsplit(",", 1))
        for entry in found.silent
    }
    if len(sources) != len(found.silent) or any(
        len(source) != LEAST or not all(source) for source in sources
    ):
        return UNNAMED
    personas = len({source[0] for source in sources})
    if not found.asked - found.answered <= personas <= found.asked:
        return SOURCES
    return None


def ended(task: Task, by: By, now: datetime, found: Found | None) -> Task:
    """The task whose newest open read by `by` ended with `found`, or, with None, in silence:
    a read with no result, which no freeze and no retry counts. With no open read, the read
    starts and ends now."""
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
