"""`lem corrections worker PATH`: one correction the hook wrote, judged by Jev and queued when it
is a lesson (`corrections.cmd_worker` on `main`).

The hook writes the owner's message into a file of its own in `corrections-waiting/` of the
state folder and starts this command detached, so the session never waits for Jev. The file is
read and removed first, so the owner's words stay in no file nobody removes. The machine's yes is
read again here, at the last moment before anything is sent: the owner may have turned the queue
off since the hook looked. A message Jev calls a lesson with a probability of FLAG_AT or more is
queued; one too long for Jev is queued with no probability, for the retro to read; a failure is
a line of the queue's log.
"""

from typing import TYPE_CHECKING

import msgspec

from lem.adapters import judge_jev_ask
from lem.addons.corrections import question, queue, switch
from lem.kernel.errors import Refusal
from lem.ports.judge import NotAsked
from lem.records.base import Frozen
from lem.records.corrections import Correction
from lem.store import places

if TYPE_CHECKING:
    from collections.abc import Mapping
    from pathlib import Path

    from lem.records.base import Moment

TOO_LONG = "too long for Jev"


class Worked(Frozen, frozen=True, kw_only=True, omit_defaults=False):
    """What became of the message: queued or not, Jev's probability, and why."""

    queued: bool
    p_lesson: float | None
    why: str


def worked(
    given: Path,
    environ: Mapping[str, str],
    now: Moment,
    asker: judge_jev_ask.Asker | None = None,
) -> Worked:
    """Judge the correction the hook wrote at `given`, and queue it when it is a lesson."""
    state = state_of(given)
    correction = taken(given)
    if not switch.says_yes(environ):
        return Worked(
            queued=False, p_lesson=None, why="the machine says no to the queue"
        )
    if not switch.repository_uses_lem(state.parent.parent):
        return Worked(
            queued=False, p_lesson=None, why="the repository has no team file"
        )
    jev = asker or question.asker_of(environ)
    return judged(state, correction, question.asked(jev, correction), now)


def state_of(given: Path) -> Path:
    """The state folder of the waiting correction `given`; refused for a file anywhere else,
    which the worker never reads or removes."""
    folder = given.parent
    state = folder.parent
    inside = folder.name == queue.WAITING and state.parent.name == ".lem"
    if not inside or given.is_symlink() or not given.is_file():
        raise Refusal(
            "not-waiting",
            f"{given} is no correction waiting in {queue.WAITING}/ of a state folder",
            "only the correction hook starts the worker, with the file it wrote",
        )
    places.workspace(state.parent.parent)
    return state


def taken(given: Path) -> Correction:
    """The correction of the file, which is removed at once."""
    body = given.read_bytes()
    given.unlink(missing_ok=True)
    try:
        return msgspec.json.decode(body, type=Correction)
    except msgspec.DecodeError as error:
        raise Refusal(
            "correction-form",
            f"{given} held no correction ({error})",
            "only the correction hook writes the file",
        ) from error


def judged(
    state: Path, correction: Correction, said: dict[str, float] | NotAsked, now: Moment
) -> Worked:
    """Queue the correction by Jev's answer, or log why there is none."""
    if isinstance(said, NotAsked) and said.why == judge_jev_ask.TOO_LONG.why:
        unjudged = msgspec.structs.replace(correction, p_lesson=None, why=TOO_LONG)
        queue.appended(state / queue.QUEUE, unjudged)
        return Worked(queued=True, p_lesson=None, why=TOO_LONG)
    if isinstance(said, NotAsked):
        why = f"jev gave no answer: {said.why}"
        stamp = now.strftime("%Y-%m-%dT%H:%M:%SZ")
        line = queue.LogLine(at=stamp, session=correction.session, error=why)
        queue.appended(state / queue.LOG, line)
        return Worked(queued=False, p_lesson=None, why=why)
    return scored(state, correction, said[question.NAME])


def scored(state: Path, correction: Correction, score: float) -> Worked:
    """Queue the correction when Jev calls it a lesson at FLAG_AT or more."""
    if score < question.FLAG_AT:
        return Worked(queued=False, p_lesson=score, why="Jev calls it no lesson")
    flagged = msgspec.structs.replace(correction, p_lesson=score)
    queue.appended(state / queue.QUEUE, flagged)
    return Worked(queued=True, p_lesson=score, why="Jev calls it a lesson")
