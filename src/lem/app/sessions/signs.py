"""The signs of work of a task's session, over its Claude Code sessions: the newest sign, whether a
shell command of it runs, whether they could be read, and whether its newest turn runs
(`signs.read_signs` on `main`).

A session's transcripts are the ones of the task (the harness's rule of the design's part 3)
whose Claude Code session the `session-start` hook put on record in that agterm session, its pane
matched in no regard to case: an old pane's `/clear`, or a line with no pane, counts for none.
Each transcript's signs come from the harness; a transcript whose signs do not read (no process
of it, or no file) gives none. The newest sign is the newest of all; the turn is that of the
transcript whose main thread wrote the newest turn; a shell of any of them is a shell of the
session. With no transcript that reads, the signs do not read, and the guard reads the task's
record alone.
"""

from functools import partial
from typing import TYPE_CHECKING

from lem.app.sessions import beside, log
from lem.records.base import Frozen, Moment
from lem.store import sessions

if TYPE_CHECKING:
    from datetime import datetime

    from lem.app.sessions.here import Here
    from lem.ports.harness import Signs, Transcript


type Pairs = tuple[tuple[Transcript, Signs], ...]


class Read(Frozen, frozen=True, kw_only=True, omit_defaults=False):
    """A session's signs of work: its newest sign, a shell command that runs, whether they
    read, and whether its newest turn runs or ended."""

    sign: Moment | None = None
    shell: bool = False
    signs: bool = False
    turn: str | None = None

    @classmethod
    def reads(cls, signs: Signs) -> bool:
        """Whether a transcript's signs read: the harness gives none for one it cannot
        read."""
        return signs.sign is not None or signs.turn is not None or signs.shell


def own_transcripts(here: Here, slug: str, session: str) -> tuple[Transcript, ...]:
    """The task's transcripts whose Claude Code session started in the agterm session
    `session`."""
    lines = sessions.read(here.folder(slug))
    claudes = {line.claude for line in lines if log.same(line.pane, session)}
    found = here.ports.harness.transcripts(slug)
    return tuple(one for one in found if one.claude in claudes)


def read_signs(here: Here, slug: str, session: str) -> Read:
    """The signs of the agterm session `session` of the task; not read when none of its
    transcripts reads."""
    harness = here.ports.harness
    found = own_transcripts(here, slug, session)
    pairs = [(one, harness.signs(one)) for one in found]
    kept = tuple(pair for pair in pairs if Read.reads(pair[1]))
    if not kept:
        return Read()
    return combined(kept, beside.main_signs(harness))


def combined(kept: Pairs, mains: beside.MainSigns) -> Read:
    """The signs of the session over its transcripts' signs that read: the newest sign of
    all, a shell of any, and the turn of the transcript whose main thread wrote the newest
    turn."""
    signs = tuple(pair[1] for pair in kept)
    newest = max(signs, key=signed)
    main = max(kept, key=partial(main_stamp, mains))[1]
    shell = any(one.shell for one in signs)
    return Read(sign=newest.sign, shell=shell, signs=True, turn=main.turn)


def main_stamp(mains: beside.MainSigns, pair: tuple[Transcript, Signs]) -> float:
    """The newest sign of a transcript's main thread, as a number to compare."""
    return stamp(mains.main_sign(pair[0]))


def signed(signs: Signs) -> float:
    """A transcript's newest sign, as a number to compare."""
    return stamp(signs.sign)


def stamp(moment: datetime | None) -> float:
    """A moment as a number to compare; 0 with none."""
    return moment.timestamp() if moment else 0
