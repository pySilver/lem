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

from lem.app.landing import merged
from lem.board.duties import forge_look
from lem.kernel.errors import Fault, Refusal
from lem.store import tasks

if TYPE_CHECKING:
    from collections.abc import Collection

    from lem.board.duties.context import Duty
    from lem.ports.forge_facts import Pull
    from lem.records.record import Record

# The board's problem of a bookkeeping that failed, by its task.
BOOKKEEPING = "merged:"


def tick(duty: Duty) -> None:
    """Look at the forge when it is due, and do the bookkeeping of each pull request that
    ended there. The merges this server runs are read before the look and again at each pull
    request: a merge that ends during the look is still left to itself."""
    running = duty.kept.running()
    numbers = numbered(tasks.every(duty.state))
    forgotten(duty, numbers.keys())
    if not numbers:
        duty.kept.problems.pop(forge_look.PROBLEM, None)
        return
    pulls = forge_look.looked(duty, numbers) if forge_look.due(duty) else None
    if pulls is None:
        return
    forge_look.written(duty, pulls)
    for slug, pull in pulls.items():
        if pull.state != "open" and not merging(duty, slug, running):
            booked(duty, slug, pull)


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


def forgotten(duty: Duty, open_tasks: Collection[str]) -> None:
    """Forget the problem of a bookkeeping whose task has no pull request open any more."""
    stale = [
        key
        for key in duty.kept.problems
        if key.startswith(BOOKKEEPING)
        and key.removeprefix(BOOKKEEPING) not in open_tasks
    ]
    for key in stale:
        duty.kept.problems.pop(key)


def booked(duty: Duty, slug: str, pull: Pull) -> None:
    """Run the bookkeeping of the pull request the forge ended, once, and again after a
    failure only when the retry's wait has passed."""
    key = ("merged", slug, str(pull.number))
    if not duty.kept.owed(key, duty.now):
        return
    told = f"pull request {pull.number} of {slug} is {pull.state} on GitHub"
    try:
        merged.run(duty.checkout, slug)
    except (Refusal, Fault) as error:
        line = (
            f"`lem land merged {slug}` failed after GitHub called pull request "
            f"{pull.number} {pull.state}: {error}; the board tries it again in a few minutes"
        )
        duty.kept.ended(key, duty.now, ran=False)
        duty.kept.problems[f"{BOOKKEEPING}{slug}"] = line
        duty.say(line)
        return
    duty.kept.done.add(key)
    duty.kept.ended(key, duty.now, ran=True)
    duty.kept.problems.pop(f"{BOOKKEEPING}{slug}", None)
    status = tasks.read(duty.state, slug).task.status
    duty.say(f"{told}; `lem land merged {slug}` left it {status}")
