"""`lem task build`: the build of a task whose plan the owner read, named by its slug or by its
plan file, whose name is the settings' `paths.plan_file` with the task's slug in it; with no
name, the plans that wait for him (the ruling "`/lem build` takes a plan file too, and lists the
waiting plans when it gets no name"). A planned task goes to `building`."""

from pathlib import PurePath
from typing import TYPE_CHECKING

from lem.app import task_reads
from lem.app.tasks import release
from lem.kernel import clock, errors
from lem.model.task import behind, holds, plans, table
from lem.records.base import Frozen
from lem.settings.load import settings_of
from lem.store import tasks

if TYPE_CHECKING:
    from lem.records.record import Record
    from lem.records.task import Task
    from lem.store.places import Workspace

PLANNED = "planned"
BUILD = "the owner's build of the plan"


class Waiting(Frozen, frozen=True, kw_only=True):
    """A task whose plan waits for the owner: its slug, his ask, and its plan."""

    slug: str
    ask: str
    plan: str | None = None


class Built(Frozen, frozen=True, kw_only=True):
    """The build that starts, or with no name, the plans that wait."""

    slug: str | None = None
    plan: str | None = None
    status: str | None = None
    waiting: tuple[Waiting, ...] = ()


def waiting(every: tuple[Record, ...]) -> tuple[Waiting, ...]:
    """The tasks whose plan waits for the owner: `planned`."""
    return tuple(
        Waiting(
            slug=record.task.slug,
            ask=record.task.ask,
            plan=record.task.plan.path if record.task.plan else None,
        )
        for record in every
        if record.task.status == PLANNED
    )


def slug_of(target: str, every: tuple[Record, ...], pattern: str) -> str | None:
    """The task a plan file names: by the plan a task has, which every record must say,
    else by the slug its name holds."""
    name = PurePath(target).name
    owners = (
        record.task.slug
        for record in every
        if record.task.plan and PurePath(record.task.plan.path).name == name
    )
    held = next(owners, None)
    if held is not None:
        return held
    named = plans.regex(pattern, None).fullmatch(name)
    return named["slug"] if named else None


def refusal(task: Task, workspace: Workspace) -> errors.Refusal | None:
    """Why a task does not build now, with the way on: his "start SLUG now" for a queued
    task, the plans that wait for one that is not planned (a view of the readable records),
    or its hold."""
    if task.status == PLANNED:
        return table.refusal(task, "building", None)
    shown = task_reads.visible(workspace.state)
    listed = ", ".join(row.slug for row in waiting(shown)) or "none"
    fix = f"build one whose plan waits (lem task build SLUG): {listed}"
    if task.status == "queued":
        fix = f"his word starts a queued task: {behind.word(task.slug)}"
    return errors.Refusal(
        "not-planned",
        f"{task.slug} is {task.status}: lem task build starts a task whose plan waits for "
        "the owner",
        fix,
    )


def started(workspace: Workspace, slug: str) -> Built:
    """Move the planned task `slug` to `building`."""
    record = release.checked(workspace.state, slug)
    refused = refusal(record.task, workspace)
    if refused is not None:
        raise refused
    now = clock.now()
    tasks.update(
        workspace.state,
        slug,
        lambda one: holds.moved(one, status="building", line=BUILD, now=now),
        record.revision,
    )
    plan = record.task.plan
    return Built(slug=slug, plan=plan.path if plan else None, status="building")


def built(workspace: Workspace, target: str | None) -> Built:
    """Start the build of the planned task `target` names, or list the plans that wait."""
    if target is None:
        return Built(waiting=waiting(task_reads.visible(workspace.state)))
    if not target.endswith(".md") and "/" not in target:
        return started(workspace, target)
    paths = settings_of(workspace.checkout).settings.paths
    slug = slug_of(target, tasks.every(workspace.state), paths.plan_file)
    if slug is None:
        raise errors.Refusal(
            "no-plan",
            f"{target} is no plan file of a task",
            "lem task build with no name lists the plans that wait",
        )
    return started(workspace, slug)
