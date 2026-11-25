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

from typing import TYPE_CHECKING

from lem.app.sessions import log
from lem.records.base import Frozen, Moment
from lem.store import sessions

if TYPE_CHECKING:
    from lem.app.sessions.here import Here
    from lem.ports.harness import Signs, Transcript


class Read(Frozen, frozen=True, kw_only=True, omit_defaults=False):
    """A session's signs of work: its newest sign, a shell command that runs, whether they
    read, and whether its newest turn runs or ended."""

    sign: Moment | None = None
    shell: bool = False
    signs: bool = False
    turn: str | None = None


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
    found = own_transcripts(here, slug, session)
    signs = [here.ports.harness.signs(one) for one in found]
    return combined(tuple(one for one in signs if read(one)))


def read(signs: Signs) -> bool:
    """Whether a transcript's signs read: the harness gives none for one it cannot read."""
    return signs.sign is not None or signs.turn is not None or signs.shell


def combined(signs: tuple[Signs, ...]) -> Read:
    """The signs of the session over its transcripts' signs that read."""
    if not signs:
        return Read()
    newest = max(signs, key=signed)
    shell = any(one.shell for one in signs)
    return Read(sign=newest.sign, shell=shell, signs=True, turn=newest.turn)


def signed(signs: Signs) -> float:
    """The moment of a transcript's newest sign, as a number to compare; 0 with none."""
    return signs.sign.timestamp() if signs.sign else 0
