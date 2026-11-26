"""A duty of the board server: the merges that are the server's to make (`merge … merger` and
`merge … owner` of `serve.duties` on `main`; the owner's ruling "The board's server runs the
merge agent's merge, and the agent only writes its review").

An open task whose merge waits for the server (`merging.merge_wait` gives `merges`: the merge
agent's review of the proposed tip says `merge`, calls nobody and asks no new round, for a
request the merge agent may merge; or the owner's merge that a moved base refused stands
through the rebase and checks) is merged by the server, as `lem land merge SLUG --by
merger|owner --via server [--standing]` does: the merge's own rules stay the gate, and the server
only runs it. Never while the forge calls the request conflicting (its session brings it onto
the base first), while a merge call waits on the forge, or while this server runs its merge. A
merge that failed waits `memory.RETRY` for the same tip and the same newest read; a new read or
a new proposal makes a new try at the next tick.
"""

from typing import TYPE_CHECKING

from lem.app.owner import forge, releases
from lem.board import merge_look
from lem.board.duties import forge_look, merge_order, merge_run, wakes
from lem.model.landing import merge_recheck, merge_standing, mergeread
from lem.records.holds import Parked, ReleaseHold
from lem.store import tasks

if TYPE_CHECKING:
    from collections.abc import Collection

    from lem.board.duties.context import Duty
    from lem.board.duties.memory import Key
    from lem.records.landing.merge import Merger
    from lem.records.record import Record


def tick(duty: Duty) -> None:
    """Wake stale approvals and start the next merge in order of the checks."""
    look = forge_look.current(duty)
    records = waiting(duty, releases.with_stops(tasks.every(duty.state)))
    bases = merge_look.bases_of(duty.here, records)
    running = duty.kept.running()
    if not running:
        for record in merge_order.ordered(bases, records):
            if start(duty, record, look, bases.for_task(record)):
                break
    for record in records:
        wake_stale(duty, record, look, bases.for_task(record), running)


def waiting(duty: Duty, records: tuple[Record, ...]) -> tuple[Record, ...]:
    """The open tasks whose next attempt does not wait for a retry."""
    opened = (record for record in records if record.task.status == "open")
    may_try = duty.kept.due
    now = duty.now
    return tuple(record for record in opened if may_try(key_of(record), now))


def start(
    duty: Duty, record: Record, look: forge.Look, basis: merge_look.MergeBasis
) -> bool:
    """Start this task when the server owns its merge."""
    if recheck(record, basis.base):
        return False
    running = duty.kept.running()
    by = merger_of(record, look, running, basis)
    return by is not None and merge_run.started(duty, record, by, key_of(record))


def merger_of(
    record: Record,
    look: forge.Look,
    running: Collection[str],
    basis: merge_look.MergeBasis = merge_look.UNKNOWN,
) -> Merger | None:
    """Who the server merges the task for now: the owner, whose merge stands, or the merge
    agent; None when its merge is not the server's to make now."""
    landing = record.landing
    if landing is None or landing.phase != "open":
        return None
    if not merge_look.server_merges(record, basis) and not recheck(record, basis.base):
        return None
    waits = landing.intent is not None or landing.accepted is not None
    held = isinstance(record.task.hold, Parked | ReleaseHold)
    if waits or held or record.task.slug in running or forge.conflicts(look, record):
        return None
    return "merger" if merge_standing.standing_of(record) is None else "owner"


def recheck(record: Record, base: str | None) -> bool:
    """Whether a newly stale approval needs its session to recheck the change."""
    landing = record.landing
    if record.task.status != "open" or landing is None or landing.refused is not None:
        return False
    return bool(
        base
        and merge_recheck.moved(landing, base)
        and merge_standing.standing_of(record)
    )


def wake_stale(
    duty: Duty,
    record: Record,
    look: forge.Look,
    basis: merge_look.MergeBasis,
    running: Collection[str],
) -> None:
    """Wake the session once for the proposed tip and the new base it must check."""
    base = basis.base
    if (
        base is None
        or not recheck(record, base)
        or merger_of(record, look, running, basis) != "owner"
    ):
        return
    slug = record.task.slug
    standing = merge_standing.standing_of(record)
    if standing is None:
        return
    key = ("recheck", slug, standing.tip, base)
    if duty.kept.owed(key, duty.now) and wakes.woken(
        duty, slug, "refused", standing.tip
    ):
        duty.kept.done.add(key)


def key_of(record: Record) -> Key:
    """What a failed merge waits under: the task, the tip Lem proposed, and the moment of the
    newest read of it, so that a new proposal or a new read tries at once."""
    landing = record.landing
    proposed = landing.proposed if landing else None
    read = mergeread.latest(landing) if landing else None
    tip = proposed.tip if proposed else ""
    at = read.at.isoformat() if read else ""
    return ("merge", record.task.slug, tip, at)
