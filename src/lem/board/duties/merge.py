"""A duty of the board server: the merges that are the server's to make (`merge … merger` and
`merge … owner` of `serve.duties` on `main`; the owner's ruling "The board's server runs the
merge agent's merge, and the agent only writes its review").

An open task whose merge waits for the server (`merging.merge_wait` gives `merges`: the merge
agent's review of the proposed tip says `merge`, calls nobody and asks no new round, for a
request the merge agent may merge; or the owner's merge that a moved base refused stands
through a new landing or a safe read) is merged by the server, as `lem land merge SLUG --by
merger|owner --via server [--standing]` does: the merge's own rules stay the gate, and the server
only runs it. Never while the forge calls the request conflicting (its session brings it onto
the base first), while a merge call waits on the forge, or while this server runs its merge. A
merge that failed waits `memory.RETRY` for the same tip and the same newest read; a new read or
a new proposal makes a new try at the next tick.
"""

from typing import TYPE_CHECKING

from lem.app.owner import forge
from lem.board.duties import merge_run
from lem.model.landing import merge_standing, mergeread, phases
from lem.model.owner import merging
from lem.records.holds import ReleaseHold
from lem.store import tasks

if TYPE_CHECKING:
    from collections.abc import Collection

    from lem.board.duties.context import Duty
    from lem.board.duties.memory import Key
    from lem.records.landing.merge import Merger
    from lem.records.record import Record


def tick(duty: Duty) -> None:
    """Start the merge of each task whose merge is the server's now."""
    look = forge.read(duty.state)
    for record in tasks.every(duty.state):
        merged(duty, record, look)


def merged(duty: Duty, record: Record, look: forge.Look) -> None:
    """Start the task's merge when it is the server's now, and no failure of it waits."""
    by = merger_of(record, look, duty.kept.running())
    key = key_of(record)
    if by is not None and duty.kept.due(key, duty.now):
        merge_run.started(duty, record, by, key)


def merger_of(
    record: Record, look: forge.Look, running: Collection[str]
) -> Merger | None:
    """Who the server merges the task for now: the owner, whose merge stands, or the merge
    agent; None when its merge is not the server's to make now."""
    landing = record.landing
    if landing is None or phases.settled(record) is not None:
        return None
    if merging.merge_wait(record) != merging.MERGES:
        return None
    waits = landing.intent is not None or landing.accepted is not None
    held = isinstance(record.task.hold, ReleaseHold)
    if waits or held or record.task.slug in running or forge.conflicts(look, record):
        return None
    return "merger" if merge_standing.standing_of(record) is None else "owner"


def key_of(record: Record) -> Key:
    """What a failed merge waits under: the task, the tip Lem proposed, and the moment of the
    newest read of it, so that a new proposal or a new read tries at once."""
    landing = record.landing
    proposed = landing.proposed if landing else None
    read = mergeread.latest(landing) if landing else None
    tip = proposed.tip if proposed else ""
    at = read.at.isoformat() if read else ""
    return ("merge", record.task.slug, tip, at)
