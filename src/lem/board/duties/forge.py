"""A duty of the board server: the look at the forge, and the bookkeeping of each pull request
the forge calls merged or closed (`serve.forge_once` on `main`).

For a pull request merged or closed on the forge the server runs what `lem land merged` runs
(`app/landing/merged.py`): a merge is written down and the task lands, a close drops it and the
branch keeps its commits. Never for a task whose merge this server runs, when the look begins or
when its pull request's turn comes: the merge's own step records the landing. A bookkeeping that
fails is the board's problem and is tried again after `memory.RETRY`; one that ran is not run
again for that pull request.
"""

from typing import TYPE_CHECKING

from lem.app.landing.pull_identity import seen
from lem.board.duties import forge_book, forge_look
from lem.model.landing import phases, queue_evidence
from lem.store import tasks

if TYPE_CHECKING:
    from lem.board.duties.context import Duty
    from lem.ports.forge_facts import Pull
    from lem.records.record import Record


def tick(duty: Duty) -> None:
    """Look at the forge when it is due, and do the bookkeeping of each pull request that
    ended there. The merges this server runs are read before the look and again at each pull
    request: a merge that ends during the look is still left to itself."""
    running = duty.kept.running()
    records = tasks.every(duty.state)
    numbers = numbered(records)
    forge_book.forgotten(duty, numbers.keys())
    recorded(duty, records, numbers, running)
    if not numbers:
        duty.kept.problems.pop(forge_look.PROBLEM, None)
        return
    pulls = forge_look.looked(duty, numbers) if forge_look.due(duty) else None
    if pulls is None:
        return
    forge_look.written(duty, pulls)
    observed(duty, pulls, running)


def recorded(
    duty: Duty,
    records: tuple[Record, ...],
    numbers: dict[str, int],
    running: frozenset[str],
) -> None:
    """Finish a merge the record already knows about, without waiting for the next poll."""
    for record in records:
        slug = record.task.slug
        due = phases.settled(record)
        if slug in numbers and due is not None and due.step == phases.MERGED:
            number = numbers.pop(slug)
            if not merging(duty, slug, running):
                forge_book.run(duty, slug, number, phases.MERGED)


def observed(duty: Duty, pulls: forge_look.Pulls, running: frozenset[str]) -> None:
    """Send a forge close, merge or confirmed dequeue to landing for bookkeeping."""
    for slug, pull in pulls.items():
        if merging(duty, slug, running):
            continue
        state = reconcile_state(duty, slug, pull)
        if state is not None:
            forge_book.run(duty, slug, pull.number, state)


def reconcile_state(duty: Duty, slug: str, pull: Pull) -> str | None:
    """The forge result to pass to the landing, if any."""
    if pull.state != "open":
        return pull.state
    if not pull.queued and not pull.dequeued:
        return None
    landing = tasks.read(duty.state, slug).landing
    return None if landing is None else queue_evidence.action(landing, seen(pull))


def merging(duty: Duty, slug: str, running: frozenset[str]) -> bool:
    """Whether this server runs the task's merge, or ran it when the look began."""
    return slug in running or slug in duty.kept.running()


def numbered(records: tuple[Record, ...]) -> dict[str, int]:
    """Each open task with a pull request, and its number."""
    found: dict[str, int] = {}
    for record in records:
        pull = record.landing.pull if record.landing else None
        if record.task.status == "open" and pull is not None:
            found[record.task.slug] = pull.number
    return found
