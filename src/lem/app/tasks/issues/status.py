"""What a step of `lem issue` asks of the project and the task before it reads the issue: a
tracker that is GitHub's, and the status the step belongs to. And the one rule of a name on
GitHub: a login or an `OWNER/REPO` is the same in either case."""

from types import MappingProxyType
from typing import TYPE_CHECKING, Literal

from lem.kernel.errors import Refusal
from lem.model.task import claim
from lem.records.holds import Parked
from lem.settings.load import settings_of

if TYPE_CHECKING:
    from pathlib import Path

    from lem.records.task import Task

type IssueStep = Literal["start", "land", "drop", "answer"]

# The status each end belongs to; the start belongs to a task neither ended nor parked.
STATUS_OF = MappingProxyType(
    {"land": "landed", "drop": "dropped", "answer": "answered"}
)
STATUS = "issue-status"


def github(checkout: Path) -> None:
    """Refuse a project whose tracker is not GitHub's."""
    tracker = settings_of(checkout).settings.tracker
    kind = tracker.kind if tracker else None
    if kind == "github":
        return
    fix = (
        "a Linear ticket's steps are the lem-linear skill's"
        if kind == "linear"
        else 'add the table [tracker] with kind = "github" to .lem/settings.toml first'
    )
    named = kind or "none"
    raise Refusal(
        "not-github-tracker",
        f"the project's tracker is {named} (.lem/settings.toml, [tracker]), and "
        'lem issue acts for kind = "github" only',
        fix,
    )


def start_refusal(task: Task, issue: str) -> Refusal | None:
    """Why the start may not run on an ended or parked task, or None."""
    parked = isinstance(task.hold, Parked)
    if task.status not in claim.ENDED and not parked:
        return None
    said = "parked" if parked else task.status
    return Refusal(
        STATUS,
        f"the task {task.slug} is {said}: the start belongs to a task whose build starts, "
        f"so nothing is written to issue {issue}",
        f"run lem issue start {task.slug} when its build starts, or leave the issue as it is",
    )


def status_refusal(task: Task, step: IssueStep, issue: str) -> Refusal | None:
    """Why the task's status does not take `step`, or None."""
    if step == "start":
        return start_refusal(task, issue)
    wanted = STATUS_OF[step]
    if task.status == wanted:
        return None
    return Refusal(
        STATUS,
        f"the task {task.slug} is {task.status}, and `lem issue {step}` belongs to a task "
        f"that is {wanted}: nothing is written to issue {issue}",
        f"run it once the task is {wanted}; lem task show {task.slug} says what it owes",
    )


def same(one: str, other: str) -> bool:
    """Whether two logins, or two `OWNER/REPO`, name one: GitHub takes either case."""
    return one.lower() == other.lower()


def others_than(logins: tuple[str, ...], login: str) -> tuple[str, ...]:
    """`logins` but `login`."""
    return tuple(found for found in logins if not same(found, login))
