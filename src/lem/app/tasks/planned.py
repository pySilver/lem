"""`lem task planned`: the plan is committed, with its count of tasks, a careful topic, and
whether it is large: the task goes from `building` to `planned`, where the plan talk runs or the
owner reads the plan, and `lem task build` takes it on."""

from functools import partial
from typing import TYPE_CHECKING

from msgspec.structs import replace

from lem.app.tasks import plans, release
from lem.kernel import clock
from lem.kernel.errors import Refusal
from lem.model.task import holds, table
from lem.store import tasks

if TYPE_CHECKING:
    from lem.records.base import Moment
    from lem.records.record import Record
    from lem.records.work import Plan
    from lem.store.places import Workspace


def with_plan(record: Record, *, plan: Plan, now: Moment) -> Record:
    """The record with its plan, moved to `planned`."""
    task = replace(record.task, plan=plan)
    line = f"plan committed: {plan.tasks} tasks"
    with_task = replace(record, task=task)
    return holds.moved(with_task, status="planned", line=line, now=now)


def plan_of(workspace: Workspace, record: Record, words: Plan) -> Plan:
    """The plan, with its path: the task's plan file; refused for a count under one and for a
    task whose plan is not written."""
    slug = record.task.slug
    if words.tasks is None or words.tasks < 1:
        raise Refusal(
            "plan-tasks",
            f"--tasks {words.tasks} counts no task: a plan holds one task at the least",
            f"lem task planned {slug} --tasks N, with N the plan's tasks",
        )
    path = plans.found(workspace, record, tasks.every(workspace.state))
    if path is None:
        raise Refusal(
            "no-plan",
            f"{slug} has no plan in its plans folder",
            f"write the plan at the path lem task plan-file {slug} gives, commit it, "
            "then run this again",
        )
    return replace(words, path=path)


def planned(workspace: Workspace, slug: str, words: Plan) -> Plan:
    """Record the plan of `slug` (`words` without its path), and move it to `planned`."""
    record = release.checked(workspace.state, slug)
    refused = table.refusal(record.task, "planned", None)
    if refused is not None:
        raise refused
    plan = plan_of(workspace, record, words)
    change = partial(with_plan, plan=plan, now=clock.now())
    tasks.update(workspace.state, slug, change, record.revision)
    return plan
