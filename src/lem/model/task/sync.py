"""The sync of a feature: while it waits `queued` for its parts, its branch takes in origin's base
by a merge commit (`docs/plans/2026-11-27-a-feature-in-parts.md`, "The sync").

A feature is a task that a part names in `Task.part_of`; it carries no key of its own. Only a
feature that waits `queued` on its branch takes a sync: once its end started, its landing's
`base` takes in the base. Each rule here takes the records and refuses with its fix.
"""

from typing import TYPE_CHECKING

from lem.kernel.errors import Refusal

if TYPE_CHECKING:
    from collections.abc import Iterable

    from lem.records.task import Task

CODE = "feature"


def named(slug: str, every: Iterable[Task]) -> bool:
    """Whether a part names the task `slug` as its feature."""
    return any(task.part_of == slug for task in every)


def refused(task: Task, *, feature: bool) -> Refusal | None:
    """Why the task may not take a sync now, or None: it is no feature, it does not wait
    `queued` for its parts, or it has no branch."""
    slug = task.slug
    if not feature:
        return Refusal(
            CODE,
            f"{slug} is no feature: no task names it with --part-of",
            "lem task sync takes the name of a feature; a task with no parts takes in the "
            f"base at its landing, with lem land base {slug}",
        )
    if task.status != "queued":
        return Refusal(
            CODE,
            f"the feature {slug} is {task.status}, and a feature takes a sync only while it "
            "waits queued for its parts",
            f"once its end started, lem land base {slug} takes in the base",
        )
    if task.branch is None:
        return Refusal(
            CODE,
            f"the feature {slug} has no branch yet",
            f"lem task worktree {slug} --branch feature/{slug} makes it; push it to origin, "
            "then run the sync again",
        )
    return None


def message(base: str, branch: str) -> str:
    """The subject of the sync's merge commit, in the form that commit message checks leave
    alone ("Merge X into Y")."""
    return f"Merge origin/{base} into {branch}"
