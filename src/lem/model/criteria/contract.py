"""The contract of a task: the criteria it is held to now, its newest approval's with each
recorded change applied, as one mark (`land.due` and `land.may_merge` on `main`, which read the
criteria as they stand at each step).

Evidence of the landing (the checks, the review, the proposal, a merge intent) is of the
contract it was made under. A new approval of other criteria, or a recorded change, moves the
mark: what was proposed for the old one may not merge as green, and the landing proposes again.
An approval of the same texts again is no move.
"""

import hashlib
from typing import TYPE_CHECKING

import msgspec

from lem.kernel.errors import Refusal
from lem.model.decisions.changes import changes_of

if TYPE_CHECKING:
    from lem.records.task import Task

LENGTH = 12


def mark(task: Task) -> str | None:
    """The mark of the task's contract: the approved track and the expected criteria's texts,
    each run of spaces as one; None for a task with no approved criteria."""
    found = changes_of(task)
    if found.approved is None or found.expected is None:
        return None
    texts = [" ".join(text.split()) for text in found.expected]
    body = msgspec.json.encode([found.approved.size, texts])
    return hashlib.sha256(body).hexdigest()[:LENGTH]


def moved(task: Task, seen: str | None) -> Refusal | None:
    """Why evidence made under the contract `seen` no longer holds, or None when the contract
    is the same."""
    now = mark(task)
    if now == seen:
        return None
    return Refusal(
        "contract-moved",
        f"the criteria of {task.slug} changed since this was made (they were {seen}, "
        f"they are {now})",
        f"the landing runs its checks and its review again on the criteria of now, and "
        f"proposes again: lem land next {task.slug} names the step",
    )
