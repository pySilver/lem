"""The signs of work of a task's session, over its Claude Code sessions: the newest sign, whether a
shell command of it runs, whether they could be read, and whether its newest turn runs
(`signs.read_signs` on `main`).

A session's transcripts are the ones of the task (the harness's rule of the design's part 3)
whose Claude Code session the `session-start` hook put on record in that agterm session, its pane
matched in no regard to case: an old pane's `/clear`, or a line with no pane, counts for none.
The newest sign is the newest of all transcripts. The turn and shell come from transcripts
whose process the harness could read. With no process that reads, the guard reads the task's
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
    from lem.ports.harness import Harness, Signs, Transcript


type Pairs = tuple[tuple[Transcript, Signs], ...]


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
    harness = here.ports.harness
    found = own_transcripts(here, slug, session)
    pairs = tuple((one, harness.signs(one)) for one in found)
    return combined(pairs, harness)


def combined(pairs: Pairs, harness: Harness) -> Read:
    """The newest transcript sign, and the turn and shell of processes that read."""
    stamps = (one.sign for _, one in pairs if one.sign is not None)
    newest = max(stamps, default=None)
    live = tuple(pair for pair in pairs if pair[1].read)
    if not live:
        return Read(sign=newest)
    main = max(live, key=partial(main_stamp, beside.main_signs(harness)))
    return Read(
        sign=newest,
        shell=any(one.shell for _, one in live),
        signs=True,
        turn=main[1].turn,
    )


def main_stamp(mains: beside.MainSigns, pair: tuple[Transcript, Signs]) -> float:
    """The newest sign of a transcript's main thread, as a number to compare."""
    return stamp(mains.main_sign(pair[0]))


def stamp(moment: datetime | None) -> float:
    """A moment as a number to compare; 0 with none."""
    return moment.timestamp() if moment else 0
