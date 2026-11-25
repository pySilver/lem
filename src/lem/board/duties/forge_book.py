"""The board's report of the landing's bookkeeping after a forge result."""

from typing import TYPE_CHECKING

from lem.app.landing import merged
from lem.board.duties import merge_said
from lem.kernel.errors import Fault, Refusal
from lem.store import tasks

if TYPE_CHECKING:
    from collections.abc import Collection

    from lem.board.duties.context import Duty
    from lem.board.duties.memory import Key

BOOKKEEPING = "merged:"
DEQUEUED = "dequeued"
QUEUED = "queued"
QUEUE_RESULTS = frozenset((DEQUEUED, QUEUED))


def forgotten(duty: Duty, open_tasks: Collection[str]) -> None:
    """Forget a bookkeeping problem whose task has no pull request open."""
    stale = [
        key
        for key in duty.kept.problems
        if key.startswith(BOOKKEEPING)
        and key.removeprefix(BOOKKEEPING) not in open_tasks
    ]
    for key in stale:
        duty.kept.problems.pop(key)


def run(duty: Duty, slug: str, number: int, state: str) -> None:
    """Run the bookkeeping once, or once per retry when it fails."""
    key = key_of(slug, number, state)
    if not duty.kept.owed(key, duty.now):
        return
    told = f"pull request {number} of {slug} is {state} on GitHub"
    try:
        outcome = merged.run(duty.checkout, slug)
    except (Refusal, Fault) as error:
        if state == DEQUEUED and isinstance(error, Refusal) and error.code == "github":
            line = merge_said.refused(duty.state, slug, error)
            duty.kept.said[slug] = line
            finished(duty, key, line)
        else:
            failed(duty, key, state, error)
        return
    status = tasks.read(duty.state, slug).task.status
    if status == "landed":
        duty.kept.said[slug] = merge_said.MERGED.format(slug=slug)
    if status == "dropped":
        duty.kept.said[slug] = (
            f"GitHub closed pull request {number} without a merge. The branch keeps its commits."
        )
    if state == QUEUED:
        duty.kept.said[slug] = merge_said.completed(slug, outcome)
    if state not in QUEUE_RESULTS:
        duty.kept.done.add(key)
    finished(duty, key, f"{told}; `lem land merged {slug}` left it {status}")


def key_of(slug: str, number: int, state: str) -> Key:
    """The bookkeeping key. A dequeue can happen before the request closes or merges."""
    closed = ("merged", slug, str(number))
    return (*closed, state) if state in QUEUE_RESULTS else closed


def finished(duty: Duty, key: Key, line: str) -> None:
    """Clear the problem and say what the bookkeeping wrote."""
    duty.kept.ended(key, duty.now, ran=True)
    duty.kept.problems.pop(problem_key(key), None)
    duty.say(line)


def failed(duty: Duty, key: Key, state: str, error: Refusal | Fault) -> None:
    """Keep the failure until the next try."""
    slug = key[1]
    number = key[2]
    why = merge_said.said_of(error)
    line = (
        f"`lem land merged {slug}` failed after GitHub called pull request "
        f"{number} {state}: {why}; the board tries it again in a few minutes"
    )
    duty.kept.ended(key, duty.now, ran=False)
    duty.kept.problems[problem_key(key)] = line
    duty.say(line)


def problem_key(key: Key) -> str:
    """The board problem keyed by task."""
    slug = key[1]
    return f"{BOOKKEEPING}{slug}"
