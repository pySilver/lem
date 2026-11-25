"""What a queued task waits for: each task named by `Task.after` that has not landed nor been
answered, and the refusal that says so (`project.cmd_may_start` on `main`). A dropped one comes
first, since only the owner's word gets past it.
"""

from typing import TYPE_CHECKING

from lem.kernel.errors import Refusal

if TYPE_CHECKING:
    from lem.records.record import Record
    from lem.records.task import Task

# The ends of a task that end a wait for it.
STARTED = frozenset(("landed", "answered"))
type Waits = tuple[tuple[str, str], ...]


def word(slug: str) -> str:
    """The command of the owner's "start SLUG now", with his words to put in."""
    return f'lem task start {slug} --words "HIS WORDS"'


def waited(task: Task, every: tuple[Record, ...]) -> Waits:
    """Each task `task` waits for that has not landed nor been answered, with its status, in
    the order of `Task.after`; `no task` for a name no record has."""
    statuses = {record.task.slug: record.task.status for record in every}
    found = {after: statuses.get(after, "no task") for after in task.after}
    return tuple(pair for pair in found.items() if pair[1] not in STARTED)


def behind(task: Task, every: tuple[Record, ...]) -> Refusal | None:
    """Why a task queued after others may not start yet, or None: a dropped one first, which
    only the owner's word gets past."""
    waits = waited(task, every)
    if not waits:
        return None
    if any(status == "dropped" for _, status in waits):
        return after_dropped(task, waits)
    return still_queued(task, waits)


def after_dropped(task: Task, waits: Waits) -> Refusal:
    """The refusal of a task queued after one that was dropped: the owner's word decides."""
    slug = task.slug
    ordered = sorted(waits, key=lambda pair: pair[1] != "dropped")
    which = ", and ".join(map(described, ordered))
    return Refusal(
        "after-dropped",
        f"{slug} is queued after {which}. A dropped task leaves it waiting for "
        f'the owner\'s word, "start {slug} now" or /lem drop {slug}',
        f"on his word, {word(slug)}; on his drop, lem task move {slug} dropped",
    )


def still_queued(task: Task, waits: Waits) -> Refusal:
    """The refusal of a task queued after tasks that run still, each with its status."""
    names = " and ".join(pair[0] for pair in waits)
    which = ", and ".join(map(described, waits))
    ends = names if len(waits) == 1 else f"each of {names}"
    return Refusal(
        "queued",
        f"{task.slug} is queued after {which}: it starts when {ends} is landed or answered",
        lifted(task, names),
    )


def described(pair: tuple[str, str]) -> str:
    """A task waited for, with its status."""
    after, status = pair
    return f"{after}, which is {status}"


def lifted(task: Task, names: str) -> str:
    """How a queue is lifted: the read again with no `--after` for a need, his word for his
    order."""
    slug = task.slug
    if task.order is not None:
        return f"only his word removes his order: {word(slug)}"
    return (
        f"when it no longer needs the result of {names}, lem task read {slug} again "
        "with no --after"
    )
