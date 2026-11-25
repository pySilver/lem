"""`lem owner away` and `lem owner back`: the owner's word on whether he is there, for every
repository on this machine (`project.cmd_owner` on `main`).

His words go into the machine's mark as he typed them; no command can tell who typed, so a stage
runs this only for words he typed in its session. A word that changes nothing writes nothing: away
while he is away, back while he is there. The tasks it names are this workspace's: after an away
the tasks that run without him, after a back the ones that came back to him (a night's never does).
"""

import os
from typing import TYPE_CHECKING

from lem.kernel import folders, paths
from lem.kernel.errors import Refusal
from lem.model.owner.presence import changed
from lem.records.base import Frozen, Moment
from lem.store import owner, places, tasks

if TYPE_CHECKING:
    from pathlib import Path

    from lem.records.task import Task


class Said(Frozen, frozen=True, kw_only=True, omit_defaults=False):
    """His presence after his word: away or there, since when, his words, whether the mark was
    written, the tasks his word changed, and the number of changes in the mark."""

    away: bool
    since: Moment | None
    words: str | None
    written: bool
    tasks: tuple[str, ...]
    seen: int


def checked(words: str | None) -> str:
    """His words as typed, without the blanks around them; refused when there are none."""
    if words is None or not words.strip():
        raise Refusal(
            "words",
            "the owner's word needs his words as typed, and no command can tell who typed",
            'lem owner away --words "I\'m away", with the words he typed in this session',
        )
    return words.strip()


def said(folder: Path, words: str | None, now: Moment, *, away: bool) -> Said:
    """Mark the owner away or back with his words, unless that changes nothing."""
    given = checked(words)
    where = places.workspace(folder)
    before = owner.read(paths.home(os.environ))
    after = before
    if before.away != away:
        home = folders.home_for_writing(os.environ)
        after = owner.change(home, given, now, away=away)
    return Said(
        away=after.away,
        since=after.since,
        words=after.words,
        written=after is not before,
        tasks=changed(tasks_of(where.state), before, after),
        seen=after.seen,
    )


def tasks_of(state: Path) -> tuple[Task, ...]:
    """Every task of the workspace."""
    return tuple(record.task for record in tasks.every(state))
