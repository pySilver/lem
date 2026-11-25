"""`lem task build`: the build of a task whose plan the owner read, named by its slug or by its
plan file, whose name is the settings' `paths.plan_file` with the task's slug in it; with no
name, the plans that wait for him (the ruling "`/lem build` takes a plan file too, and lists the
waiting plans when it gets no name"). A planned task goes to `building`."""

from functools import partial
from pathlib import PurePath
from typing import TYPE_CHECKING

from lem.app.tasks import plans, release
from lem.kernel import clock, errors
from lem.model.task import holds, queue, table
from lem.model.task import plans as names
from lem.records.base import Frozen
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
    """The task a target names: a slug as it is; a plan file by the plan a task has, else by
    the slug its name holds."""
    if not target.endswith(".md") and "/" not in target:
        return target
    name = PurePath(target).name
    owners = (
        record.task.slug
        for record in every
        if record.task.plan and PurePath(record.task.plan.path).name == name
    )
    held = next(owners, None)
    if held is not None:
        return held
    named = names.regex(pattern, None).fullmatch(name)
    return named["slug"] if named else None


def refusal(task: Task, every: tuple[Record, ...]) -> errors.Refusal | None:
    """Why a task does not build now, with the way on: his "start SLUG now" for a queued
    task, the plans that wait for one that is not planned, or its hold."""
    if task.status == PLANNED:
        return table.refusal(task, "building", None)
    listed = ", ".join(row.slug for row in waiting(every)) or "none"
    fix = f"build one whose plan waits (lem task build SLUG): {listed}"
    if task.status == "queued":
        fix = f"his word starts a queued task: {queue.word(task.slug)}"
    return errors.Refusal(
        "not-planned",
        f"{task.slug} is {task.status}: lem task build starts a task whose plan waits for "
        "the owner",
        fix,
    )


def started(workspace: Workspace, slug: str, every: tuple[Record, ...]) -> Built:
    """Move the planned task `slug` to `building`."""
    record = release.checked(workspace.state, slug)
    refused = refusal(record.task, every)
    if refused is not None:
        raise refused
    change = partial(holds.moved, status="building", line=BUILD, now=clock.now())
    tasks.update(workspace.state, slug, change, record.revision)
    plan = record.task.plan
    return Built(slug=slug, plan=plan.path if plan else None, status="building")


def built(workspace: Workspace, target: str | None) -> Built:
    """Start the build of the planned task `target` names, or list the plans that wait."""
    every = tasks.every(workspace.state)
    if target is None:
        return Built(waiting=waiting(every))
    slug = slug_of(target, every, plans.paths_of(workspace.checkout).plan_file)
    if slug is None:
        raise errors.Refusal(
            "no-plan",
            f"{target} is no plan file of a task",
            "lem task build with no name lists the plans that wait",
        )
    return started(workspace, slug, every)
