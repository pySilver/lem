"""A part of a feature: a task whose `Task.part_of` names the feature, and whose base is the
feature's branch until its landing records one (`docs/plans/2026-11-27-a-feature-in-parts.md`,
section 3).

A part is opened only beside a feature that is `queued` with its branch on origin, and that is
no part itself; a part takes no ticket of its own, since the feature holds it. Once open, a part
starts from the feature's branch only while the feature has not ended and origin has that
branch. Each rule here takes the records and the facts git gave, and refuses with its fix.
"""

from typing import TYPE_CHECKING

from lem.kernel.errors import Refusal
from lem.model.task.claim import ENDED

if TYPE_CHECKING:
    from lem.records.task import Task

CODE = "part-of"
DROP = "the owner drops {part} with /lem drop {part}"


def ticketed(part: str) -> Refusal:
    """The refusal of `--ticket` beside `--part-of`: only the feature holds a ticket."""
    return Refusal(
        CODE,
        f"{part} is to be a part of a feature, and only the feature holds a ticket",
        "leave out --ticket: the feature's ticket stands for each of its parts",
    )


def same_part(task: Task, feature: str | None) -> Refusal | None:
    """Why a retry of the open may not pass, or None: its `--part-of` is not the feature the
    task holds."""
    if task.part_of == feature:
        return None
    held = f"a part of {task.part_of}" if task.part_of else "no part of a feature"
    return Refusal(
        "task-exists",
        f"the task {task.slug} is {held} already, and a task's feature is written once",
        "this is another request under the same name: add a word to the slug",
    )


def unread(part: str, feature: str, said: str) -> Refusal:
    """The refusal of a part whose feature has no record that reads."""
    return Refusal(
        CODE,
        f"{part} is a part of {feature}, and the record of {feature} does not read: {said}",
        f"lem task show {feature} names what is wrong with it; or "
        + DROP.format(part=part),
    )


def joinable(part: str, feature: Task) -> Refusal | None:
    """Why a new part may not join `feature`, or None: a feature waits `queued` for its
    parts, and a part has no parts of its own."""
    if feature.part_of is not None:
        return Refusal(
            CODE,
            f"{feature.slug} is a part of {feature.part_of}, and a part has no parts of its "
            "own",
            f"open {part} with --part-of {feature.part_of}, or as a task of its own",
        )
    if feature.status != "queued":
        return Refusal(
            CODE,
            f"{feature.slug} is {feature.status}, and a part joins only a feature that is "
            "queued and waits for its parts",
            f"open {part} as a task of its own, or as a part of a feature that is queued",
        )
    return None


def startable(part: str, feature: Task) -> Refusal | None:
    """Why a part may not start from its feature's branch, or None: the feature ended."""
    if feature.status not in ENDED:
        return None
    return Refusal(
        CODE,
        f"{part} is a part of {feature.slug}, which is {feature.status}, so nothing lands on "
        "its branch any more",
        f"{DROP.format(part=part)}, or asks for its work again as a task of its own",
    )


def no_branch(part: str, feature: Task) -> Refusal:
    """The refusal of a part whose feature has no branch on origin."""
    branch = feature.branch
    if branch is None:
        return Refusal(
            CODE,
            f"{part} is a part of {feature.slug}, and {feature.slug} has no branch yet",
            f"lem task worktree {feature.slug} makes its branch; push it to origin, then "
            "run the step again",
        )
    return Refusal(
        CODE,
        f"{part} is a part of {feature.slug}, and origin has no branch {branch}",
        f"push {branch} to origin, then run the step again; or "
        + DROP.format(part=part),
    )
